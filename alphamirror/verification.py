"""
Phase 2: Verify candidate wallets.

Since AVE's /address/smart_wallet/list already returns profit + win rate +
profit-tier distribution + volume + recency, we don't re-derive those from
per-holding P&L calls. Instead, verification stress-tests that data against
independent signals:

  1. wallet_info   → wallet age (anti-sybil)
  2. wallet_tokens → current portfolio snapshot (are they still in the game?)

That's 2 API calls per candidate instead of ~7. At free-tier 1 TPS this means
verifying 10 candidates in ~20 seconds instead of 70.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable, Iterable, Optional

from .ave_client import AveApiError
from .models import Candidate, Holding, VerifiedWallet
from .scoring import score_wallet

ProgressFn = Callable[[str], None]


def verify_one(
    ave,
    candidate: Candidate,
    on_progress: Optional[ProgressFn] = None,
) -> VerifiedWallet:
    """Run verification for a single candidate. Returns scored VerifiedWallet."""
    addr = candidate.address
    chain = candidate.chain

    _report(on_progress, f"  [1/2] wallet_info {addr[:10]}...")
    info_raw = _safe_call(ave.wallet_info, addr, chain) or {}
    age_days = _extract_age_days(info_raw)

    _report(on_progress, f"  [2/2] wallet_tokens {addr[:10]}...")
    tokens_raw = _safe_call(ave.wallet_tokens, addr, chain, hide_sold=True) or []
    holdings = [Holding.from_api(t) for t in tokens_raw if t]

    total_value = sum(h.balance_usd for h in holdings)
    blue_chip_value = sum(h.balance_usd for h in holdings if h.is_blue_chip)
    bc_ratio = (blue_chip_value / total_value) if total_value > 0 else 0.0

    verified = VerifiedWallet(
        candidate=candidate,
        age_days=age_days,
        portfolio_value_usd=total_value,
        portfolio_size=len(holdings),
        blue_chip_ratio=bc_ratio,
        holdings=holdings,
    )
    return score_wallet(verified)


def verify_all(
    ave,
    candidates: Iterable[Candidate],
    on_progress: Optional[ProgressFn] = None,
) -> list[VerifiedWallet]:
    """Verify a batch of candidates. Results sorted by score desc."""
    cs = list(candidates)
    results: list[VerifiedWallet] = []
    for idx, c in enumerate(cs, start=1):
        _report(on_progress, f"[{idx}/{len(cs)}] Verifying {c.address[:10]}...")
        results.append(verify_one(ave, c, on_progress=on_progress))
    results.sort(key=lambda w: w.score, reverse=True)
    return results


# ---------- helpers ----------


def _safe_call(fn, *args, **kwargs):
    """Return None on API errors so one bad wallet doesn't break the batch."""
    try:
        return fn(*args, **kwargs)
    except AveApiError:
        return None


def _extract_age_days(info: dict) -> Optional[int]:
    """
    Extract wallet age in days from an /address/walletinfo response.

    AVE's real shape (confirmed by live inspection):
        "wallet_age": "1758881259"   # Unix timestamp SECONDS, first activity

    Heuristic: if the numeric value is >= 10^9, it's a Unix timestamp (seconds),
    convert to days-since-now. Otherwise treat as an explicit day count.
    """
    now = int(time.time())

    # Preferred: timestamp-based fields
    for key in ("wallet_age", "first_tx_time", "first_seen_at",
                "created_at", "first_active_time"):
        v = info.get(key)
        if v in (None, "", 0):
            continue
        if isinstance(v, str):
            # ISO 8601 string?
            try:
                dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                now_dt = datetime.now(timezone.utc)
                return max(0, (now_dt - dt).days)
            except ValueError:
                pass
            # Numeric string?
            try:
                v = float(v)
            except ValueError:
                continue
        if isinstance(v, (int, float)):
            n = int(v)
            if n >= 1_000_000_000:  # looks like a Unix timestamp (seconds)
                return max(0, (now - n) // 86400)
            if 0 < n < 100_000:  # looks like a day count (< ~270 years)
                return n

    # Fallback: explicit day-count fields
    for key in ("age_days", "first_seen_days", "age"):
        v = info.get(key)
        if v is None:
            continue
        try:
            return int(v)
        except (TypeError, ValueError):
            continue
    return None


def _report(fn: Optional[ProgressFn], msg: str) -> None:
    if fn:
        fn(msg)
