"""
AVE Cloud REST API client — free tier compatible.

Base URL: https://data.ave-api.xyz/v2
Auth: X-API-KEY header
Rate limit: 1 TPS on free tier (enforced client-side before every call).

Only endpoints AlphaMirror needs are exposed — this is not a full AVE SDK.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

V2_BASE = "https://data.ave-api.xyz/v2"

# From AVE config.py source: plan → requests/sec
RPS_BY_PLAN = {"free": 1.0, "normal": 5.0, "pro": 20.0}


class AveApiError(RuntimeError):
    """Raised for non-2xx HTTP responses or malformed payloads."""

    def __init__(self, status: int, message: str):
        super().__init__(f"AVE API {status}: {message}")
        self.status = status


class _RateLimiter:
    """
    Thread-safe minimum-interval limiter.
    Free tier is 1 TPS; parallelism would hit rate limit errors from the server,
    so all requests serialize through this lock.
    """

    def __init__(self, rps: float):
        self._min_interval = 1.0 / rps
        self._last = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last = time.monotonic()


class AveClient:
    """
    Thin REST wrapper over AVE Cloud Data v2 API.

    Usage:
        with AveClient() as ave:
            results = ave.search("PEPE", chain="bsc")
            smart = ave.smart_wallets(chain="bsc")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        plan: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("AVE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AVE_API_KEY not set. Get one at https://cloud.ave.ai and "
                "add it to .env"
            )

        plan = plan or os.environ.get("API_PLAN", "free")
        rps = RPS_BY_PLAN.get(plan, 1.0)
        self._limiter = _RateLimiter(rps)

        self._client = httpx.Client(
            base_url=V2_BASE,
            headers={
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    # ---------- lifecycle ----------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AveClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # ---------- low-level ----------

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        self._limiter.wait()
        r = self._client.get(path, params=_clean(params))
        return _unwrap(r)

    def _post(self, path: str, body: dict) -> Any:
        self._limiter.wait()
        r = self._client.post(path, json=body)
        return _unwrap(r)

    # ---------- token discovery ----------

    def search(
        self, keyword: str, chain: Optional[str] = None, limit: int = 20
    ) -> list[dict]:
        """Search tokens by keyword. Returns list of token dicts."""
        return self._get(
            "/tokens",
            {"keyword": keyword, "limit": limit, "chain": chain},
        ) or []

    def trending(self, chain: str, page: int = 0, page_size: int = 20) -> list[dict]:
        """Current trending tokens on a chain (latest snapshot only)."""
        return self._get(
            "/tokens/trending",
            {"chain": chain, "page": page, "page_size": page_size},
        ) or []

    # ---------- token detail ----------

    def token(self, address: str, chain: str) -> dict:
        """Full token info: price, liq, volume, pairs."""
        return self._get(f"/tokens/{address}-{chain}") or {}

    def holders(
        self, address: str, chain: str, limit: int = 100
    ) -> list[dict]:
        """Top holders snapshot. Free tier max 100."""
        return self._get(
            f"/tokens/holders/{address}-{chain}",
            {"limit": limit, "sort_by": "balance", "order": "desc"},
        ) or []

    def risk(self, address: str, chain: str) -> dict:
        """Contract security / honeypot report."""
        return self._get(f"/contracts/{address}-{chain}") or {}

    def kline_token(
        self,
        address: str,
        chain: str,
        interval: int = 60,
        limit: int = 24,
    ) -> list[list]:
        """OHLCV candles for a token. Interval in seconds."""
        return self._get(
            f"/klines/token/{address}-{chain}",
            {"interval": interval, "limit": limit},
        ) or []

    def txs(self, pair_address: str, chain: str) -> list[dict]:
        """Recent swap transactions on a pair."""
        return self._get(f"/txs/{pair_address}-{chain}") or []

    # ---------- wallet intelligence (AlphaMirror's core) ----------

    def smart_wallets(
        self,
        chain: str,
        keyword: Optional[str] = None,
        sort: str = "pnl_7d",
        sort_dir: str = "desc",
    ) -> list[dict]:
        """
        AVE's built-in smart-money classifier.
        We take this as a candidate pool, then verify each with address_pnl.
        """
        return self._get(
            "/address/smart_wallet/list",
            {
                "chain": chain,
                "keyword": keyword,
                "sort": sort,
                "sort_dir": sort_dir,
            },
        ) or []

    def wallet_info(self, wallet: str, chain: str) -> dict:
        """Wallet metadata: age, reputation, labels."""
        return self._get(
            "/address/walletinfo",
            {"wallet_address": wallet, "chain": chain},
        ) or {}

    def wallet_tokens(
        self,
        wallet: str,
        chain: str,
        sort: str = "value",
        hide_sold: bool = True,
        blue_chips: bool = False,
        page_size: int = 50,
    ) -> list[dict]:
        """
        Current token holdings of a wallet.
        Polled periodically in monitor phase to detect new positions.
        """
        return self._get(
            "/address/walletinfo/tokens",
            {
                "wallet_address": wallet,
                "chain": chain,
                "sort": sort,
                "hide_sold": 1 if hide_sold else 0,
                "blue_chips": 1 if blue_chips else 0,
                "pageSize": page_size,
            },
        ) or []

    def address_pnl(
        self, wallet: str, chain: str, token_address: str
    ) -> dict:
        """
        Realized + unrealized P&L of a wallet on a specific token.
        This is the core verification primitive — 1 call gives us the truth.
        """
        return self._get(
            "/address/pnl",
            {
                "wallet_address": wallet,
                "chain": chain,
                "token_address": token_address,
            },
        ) or {}

    def address_txs(
        self,
        wallet: str,
        chain: str,
        token: Optional[str] = None,
        page_size: int = 50,
    ) -> list[dict]:
        """Wallet transaction history (optionally scoped to one token)."""
        return self._get(
            "/address/tx",
            {
                "wallet_address": wallet,
                "chain": chain,
                "token": token,
                "page_size": page_size,
            },
        ) or []


# ---------- helpers ----------


def _clean(params: Optional[dict]) -> dict:
    """Drop None values so we don't send empty query params."""
    if not params:
        return {}
    return {k: v for k, v in params.items() if v is not None}


def _unwrap(r: httpx.Response) -> Any:
    """
    Unwrap AVE's envelope response. Common shape: {status, msg, data, ...}.
    We return `data` if present, otherwise the raw JSON.
    """
    if r.status_code >= 400:
        raise AveApiError(r.status_code, r.text[:300])

    try:
        js = r.json()
    except ValueError:
        raise AveApiError(r.status_code, f"non-JSON: {r.text[:300]}")

    if isinstance(js, dict) and "data" in js:
        # status field is 1 for success in AVE's convention, but some endpoints
        # omit it; treat presence of `data` as authoritative.
        return js["data"]
    return js
