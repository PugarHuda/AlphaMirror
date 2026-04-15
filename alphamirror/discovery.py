"""
Phase 1: Discover candidate smart-money wallets.

Single API call: AVE's /address/smart_wallet/list. We trust AVE's classification
as a *candidate pool* only — Phase 2 (verification) will re-check each with
hard P&L numbers.

This module is intentionally thin. The innovation is in Phase 2.
"""

from __future__ import annotations

from typing import Optional

from .ave_client import AveClient
from .models import Candidate


def discover_candidates(
    ave: AveClient,
    chain: str,
    keyword: Optional[str] = None,
    sort: str = "pnl_7d",
    max_candidates: int = 10,
) -> list[Candidate]:
    """
    Fetch candidate smart-money wallets from AVE and return a capped list.

    `max_candidates` matters because each candidate in Phase 2 will cost
    multiple API calls (wallet_info + wallet_tokens + N × address_pnl).
    On free tier (1 TPS), verifying 10 candidates takes roughly 2-3 minutes.
    """
    raw = ave.smart_wallets(chain=chain, keyword=keyword, sort=sort, sort_dir="desc")
    candidates = [Candidate.from_api(r, chain=chain) for r in raw]
    # Filter out entries with no address (defensive against API shape drift)
    candidates = [c for c in candidates if c.address]
    return candidates[:max_candidates]
