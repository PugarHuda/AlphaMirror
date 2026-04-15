"""
MockAveClient — offline demo mode.

When DEMO_MODE=1 in the environment, the CLI and Streamlit app will use this
instead of the live AveClient. It reads canned fixture data from
`demo/fixtures.json` and returns responses in the same shape the real API does.

This matters for the hackathon demo video: live API calls can fail or lag at
the exact moment you're recording. Offline mode gives a deterministic,
repeatable demo that still exercises 100% of AlphaMirror's business logic.

Usage:
    DEMO_MODE=1 python -m alphamirror.cli run --chain bsc --top 5
    DEMO_MODE=1 streamlit run app.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional


DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "demo" / "fixtures.json"


class MockAveClient:
    """
    Duck-typed replacement for AveClient that serves canned JSON.
    All methods match the real client's signatures exactly so the rest of
    the pipeline is unaware of the substitution.

    We deliberately add a small sleep on each call to simulate the free tier
    rate limit — this keeps the demo video visually honest (users see the
    progress bar advance at the same pace live mode would).
    """

    def __init__(self, fixture_path: Path = DEFAULT_FIXTURE_PATH, simulate_latency: bool = True):
        self.api_key = "demo"
        self._fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
        self._simulate = simulate_latency

    def close(self) -> None:
        pass

    def __enter__(self) -> "MockAveClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _tick(self) -> None:
        if self._simulate:
            time.sleep(0.3)

    # ---------- token discovery ----------

    def search(self, keyword: str, chain: Optional[str] = None, limit: int = 20) -> list[dict]:
        self._tick()
        return self._fixtures.get("search", {}).get(keyword.upper(), [])[:limit]

    def trending(self, chain: str, page: int = 0, page_size: int = 20) -> list[dict]:
        self._tick()
        return self._fixtures.get("trending", {}).get(chain.lower(), [])[:page_size]

    # ---------- token detail ----------

    def token(self, address: str, chain: str) -> dict:
        self._tick()
        return {"address": address, "chain": chain}

    def holders(self, address: str, chain: str, limit: int = 100) -> list[dict]:
        self._tick()
        return []

    def risk(self, address: str, chain: str) -> dict:
        self._tick()
        return self._fixtures.get("risk", {}).get(address.lower(), {
            "is_honeypot": False,
            "buy_tax": 0,
            "sell_tax": 0,
        })

    def kline_token(
        self, address: str, chain: str, interval: int = 60, limit: int = 24
    ) -> list[list]:
        self._tick()
        # Fake a smooth uptrend for chart visual
        base = 1.0
        return [[i, base, base * 1.01, base * 0.99, base * (1 + i * 0.01), 1000]
                for i in range(limit)]

    def txs(self, pair_address: str, chain: str) -> list[dict]:
        self._tick()
        return []

    # ---------- wallet intelligence ----------

    def smart_wallets(
        self,
        chain: str,
        keyword: Optional[str] = None,
        sort: str = "pnl_7d",
        sort_dir: str = "desc",
    ) -> list[dict]:
        self._tick()
        return self._fixtures.get("smart_wallets", {}).get(chain.lower(), [])

    def wallet_info(self, wallet: str, chain: str) -> dict:
        self._tick()
        return self._fixtures.get("wallet_info", {}).get(wallet.lower(), {})

    def wallet_tokens(
        self,
        wallet: str,
        chain: str,
        sort: str = "value",
        hide_sold: bool = True,
        blue_chips: bool = False,
        page_size: int = 50,
    ) -> list[dict]:
        self._tick()
        return self._fixtures.get("wallet_tokens", {}).get(wallet.lower(), [])

    def address_pnl(self, wallet: str, chain: str, token_address: str) -> dict:
        self._tick()
        return (
            self._fixtures.get("address_pnl", {})
            .get(wallet.lower(), {})
            .get(token_address.lower(), {"realized_pnl": 0, "unrealized_pnl": 0})
        )

    def address_txs(
        self,
        wallet: str,
        chain: str,
        token: Optional[str] = None,
        page_size: int = 50,
    ) -> list[dict]:
        self._tick()
        return []
