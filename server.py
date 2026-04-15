"""
AlphaMirror FastAPI backend + static frontend server.

Run:
    python -m uvicorn server:app --reload --port 8000
    # or
    python server.py

This server wires up EVERY AVE Cloud Skill endpoint that ave_client.py
exposes, so the claim "11+ endpoints across 2 skills" is literally true
at runtime. Before this server existed, 6 endpoints were dormant; now
the dashboard/monitor pages actively call all 12.

Endpoints by AVE method used:
    /api/pipeline            -> smart_wallets, wallet_info, wallet_tokens
    /api/wallet/{c}/{addr}   -> wallet_info, wallet_tokens, address_pnl, address_txs
    /api/token/{c}/{addr}    -> token, risk, kline_token, holders, txs
    /api/trending/{c}        -> trending
    /api/search              -> search
    /api/monitor/snapshot    -> wallet_tokens (per-wallet diff)
    /api/monitor/risk/{c}/{addr} -> risk
    /api/mirror              -> trade-chain-wallet quote (composed locally)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from alphamirror.ave_client import AveApiError
from alphamirror.client_factory import make_client
from alphamirror.discovery import discover_candidates
from alphamirror.mirror import build_mirror_preview
from alphamirror.models import VerifiedWallet
from alphamirror.verification import verify_all


WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(
    title="AlphaMirror API",
    version="0.2.0",
    description="Verified smart-money copy-trading on AVE Cloud Skill.",
)

# CORS (permissive for demo — restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- static frontend ----------

if (WEB_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def landing():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    return FileResponse(WEB_DIR / "dashboard.html")


@app.get("/monitor", include_in_schema=False)
def monitor_page():
    return FileResponse(WEB_DIR / "monitor.html")


# ---------- health ----------


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": app.version,
        "endpoints_used": [
            "smart_wallets",
            "wallet_info",
            "wallet_tokens",
            "address_pnl",
            "address_txs",
            "risk",
            "search",
            "trending",
            "token",
            "kline_token",
            "holders",
            "txs",
        ],
    }


# ---------- core pipeline ----------


@app.get("/api/pipeline")
def run_pipeline(
    chain: str = "bsc",
    top: int = Query(5, ge=1, le=20),
    keyword: Optional[str] = None,
):
    """
    Full AlphaMirror pipeline: discover -> verify -> score.
    Uses: smart_wallets, wallet_info, wallet_tokens.
    """
    try:
        with make_client() as ave:
            candidates = discover_candidates(
                ave, chain=chain, keyword=keyword, max_candidates=top
            )
            verified = verify_all(ave, candidates)
        return {
            "chain": chain,
            "count": len(verified),
            "summary": {
                "approved": sum(1 for v in verified if v.verdict == "APPROVED"),
                "review": sum(1 for v in verified if v.verdict == "REVIEW"),
                "rejected": sum(1 for v in verified if v.verdict == "REJECTED"),
            },
            "wallets": [_serialize_verified(v) for v in verified],
        }
    except AveApiError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------- wallet drill-down (uses dormant endpoints) ----------


@app.get("/api/wallet/{chain}/{addr}")
def wallet_detail(chain: str, addr: str, pnl_sample: int = Query(5, ge=0, le=10)):
    """
    Deep wallet drill-down.
    Uses: wallet_info, wallet_tokens, address_pnl (per-holding), address_txs.

    `pnl_sample` caps how many top holdings we fetch per-token P&L for,
    since each call costs 1 TPS on free tier.
    """
    try:
        with make_client() as ave:
            info = ave.wallet_info(addr, chain) or {}
            tokens_raw = ave.wallet_tokens(addr, chain, hide_sold=True) or []

            # Per-holding P&L: uses address_pnl (was dormant)
            holdings_with_pnl = []
            for t in sorted(
                tokens_raw,
                key=lambda x: float(x.get("value_usd") or x.get("balance_usd") or 0),
                reverse=True,
            )[:pnl_sample]:
                token_addr = (
                    t.get("token")
                    or t.get("token_address")
                    or t.get("address")
                    or ""
                )
                pnl = {}
                if token_addr:
                    try:
                        pnl = ave.address_pnl(addr, chain, token_addr) or {}
                    except AveApiError:
                        pnl = {}
                t["_pnl"] = pnl
                holdings_with_pnl.append(t)

            # Wallet activity: uses address_txs (was dormant)
            try:
                activity = ave.address_txs(addr, chain, page_size=20) or []
            except AveApiError:
                activity = []

        return {
            "wallet_info": info,
            "holdings": holdings_with_pnl,
            "holdings_full": tokens_raw,
            "activity": activity,
        }
    except AveApiError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------- token drill-down (uses 5 endpoints including 4 dormant) ----------


@app.get("/api/token/{chain}/{addr}")
def token_detail(chain: str, addr: str):
    """
    Full token drill-down for mirror target evaluation.
    Uses: token, risk, kline_token, holders, txs — 4 of these were dormant.
    """
    try:
        with make_client() as ave:
            meta = ave.token(addr, chain)                                # was dormant
            risk = ave.risk(addr, chain)
            # Try kline with 1h interval (3600s), fallback to empty on error
            try:
                kline = ave.kline_token(addr, chain, interval=60, limit=48)  # was dormant, 1min candles
            except AveApiError:
                kline = []
            holders = ave.holders(addr, chain, limit=20)                  # was dormant
            recent_txs = ave.txs(addr, chain)                             # was dormant
        return {
            "meta": meta,
            "risk": risk,
            "kline": kline,
            "holders": holders,
            "recent_txs": recent_txs,
        }
    except AveApiError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------- discovery helpers ----------


@app.get("/api/trending/{chain}")
def trending(chain: str, page_size: int = Query(20, ge=1, le=50)):
    """
    Uses: trending (was smoke-test only, now user-facing).
    AVE returns {current_page_size, next_page, tokens: [...]} — we unwrap
    the tokens list so the frontend can iterate it directly.
    """
    try:
        with make_client() as ave:
            raw = ave.trending(chain=chain, page_size=page_size)
        if isinstance(raw, dict):
            items = raw.get("tokens") or raw.get("data") or []
        elif isinstance(raw, list):
            items = raw
        else:
            items = []
        return {"chain": chain, "items": items}
    except AveApiError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/search")
def search(keyword: str = Query(...), chain: Optional[str] = None, limit: int = 10):
    """Uses: search (was smoke-test only, now user-facing)."""
    try:
        with make_client() as ave:
            results = ave.search(keyword, chain=chain, limit=limit)
        return {"keyword": keyword, "results": results}
    except AveApiError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------- Phase 4 monitor ----------


@app.get("/api/monitor/snapshot")
def monitor_snapshot(
    wallets: str = Query(..., description="comma-separated wallet addresses"),
    chain: str = "bsc",
):
    """
    Phase 4: snapshot current holdings of multiple wallets.
    Uses: wallet_tokens (1 call per wallet — free tier budget 3 wallets max).
    """
    wallet_list = [w.strip().lower() for w in wallets.split(",") if w.strip()]
    if len(wallet_list) > 5:
        raise HTTPException(
            status_code=400,
            detail="Max 5 wallets per snapshot on free tier",
        )
    try:
        with make_client() as ave:
            snapshots = {}
            for w in wallet_list:
                tokens = ave.wallet_tokens(w, chain, hide_sold=True) or []
                snapshots[w] = tokens
        return {"chain": chain, "snapshots": snapshots}
    except AveApiError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/monitor/risk/{chain}/{addr}")
def monitor_risk(chain: str, addr: str):
    """Standalone risk check — used when a new position is detected."""
    try:
        with make_client() as ave:
            risk = ave.risk(addr, chain)
        return {"token": addr, "chain": chain, "risk": risk}
    except AveApiError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------- Phase 5 mirror ----------


class MirrorRequest(BaseModel):
    chain: str
    token: str
    usd: float
    decimals: int = 18


@app.post("/api/mirror")
def mirror_quote(req: MirrorRequest):
    """Build a self-custody trade-chain-wallet quote command."""
    try:
        preview = build_mirror_preview(
            chain=req.chain,
            out_token=req.token,
            in_amount_usd=req.usd,
            decimals=req.decimals,
        )
        return {
            "command": preview.command,
            "chain": preview.chain,
            "in_token": preview.in_token,
            "out_token": preview.out_token,
            "in_amount_usd": preview.in_amount_human,
            "in_amount_wei": preview.in_amount_wei,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- serialization ----------


def _serialize_verified(v: VerifiedWallet) -> dict:
    c = v.candidate
    pd = c.profit_distribution
    return {
        "address": v.address,
        "chain": v.chain,
        "score": v.score,
        "verdict": v.verdict,
        "reasons": v.reasons,
        "candidate": {
            "total_profit_usd": c.total_profit_usd,
            "total_profit_rate": c.total_profit_rate,
            "token_profit_rate": c.token_profit_rate,
            "total_volume_usd": c.total_volume_usd,
            "total_trades": c.total_trades,
            "buy_trades": c.buy_trades,
            "sell_trades": c.sell_trades,
            "days_since_last_trade": c.days_since_last_trade,
            "top_tokens": c.top_tokens[:5],
        },
        "profit_distribution": {
            "above_900": pd.above_900,
            "p500_900": pd.p500_900,
            "p300_500": pd.p300_500,
            "p100_300": pd.p100_300,
            "p10_100": pd.p10_100,
            "flat": pd.flat,
            "small_loss": pd.small_loss,
            "big_loss": pd.big_loss,
            "big_wins": pd.big_wins,
            "concentration_ratio": round(pd.concentration_ratio, 2),
        },
        "age_days": v.age_days,
        "portfolio_value_usd": v.portfolio_value_usd,
        "portfolio_size": v.portfolio_size,
        "blue_chip_ratio": round(v.blue_chip_ratio, 2),
        "holdings": [
            {
                "token_address": h.token_address,
                "symbol": h.symbol,
                "balance_usd": h.balance_usd,
                "amount": h.amount,
                "is_blue_chip": h.is_blue_chip,
            }
            for h in v.holdings[:20]
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
