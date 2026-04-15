"""
Typed domain models for AlphaMirror.

Field names follow the real AVE API shape (discovered by live inspection on
2026-04-15), not earlier guesses. The parsers are tolerant enough that minor
field renames on AVE's side won't break things.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ProfitDistribution:
    """
    Count of trades by profit tier — AVE's per-token profit histogram.

    This is the high-signal data that lets us distinguish:
      - "one-hit wonder" (all profit from 1 × 10x trade)
      - "consistent alpha" (several 2-5x wins across many trades)
      - "mediocre" (mostly flat ±10% trades)
    """

    above_900: int = 0        # > 10x wins (legendary)
    p500_900: int = 0         # 5-10x
    p300_500: int = 0         # 3-5x
    p100_300: int = 0         # 2-4x (strong)
    p10_100: int = 0          # 1.1-2x (small wins)
    flat: int = 0             # -10 .. +10%
    small_loss: int = 0       # -10 .. -50%
    big_loss: int = 0         # -50 .. -100%

    @classmethod
    def from_api(cls, d: dict) -> "ProfitDistribution":
        return cls(
            above_900=_i(d.get("profit_above_900_percent_num")),
            p500_900=_i(d.get("profit_500_900_percent_num")),
            p300_500=_i(d.get("profit_300_500_percent_num")),
            p100_300=_i(d.get("profit_100_300_percent_num")),
            p10_100=_i(d.get("profit_10_100_percent_num")),
            flat=_i(d.get("profit_neg10_10_percent_num")),
            small_loss=_i(d.get("profit_neg50_neg10_percent_num")),
            big_loss=_i(d.get("profit_neg100_neg50_percent_num")),
        )

    @property
    def total(self) -> int:
        return (
            self.above_900 + self.p500_900 + self.p300_500 + self.p100_300
            + self.p10_100 + self.flat + self.small_loss + self.big_loss
        )

    @property
    def big_wins(self) -> int:
        """Trades that returned 2x or more."""
        return self.above_900 + self.p500_900 + self.p300_500 + self.p100_300

    @property
    def any_wins(self) -> int:
        return self.big_wins + self.p10_100

    @property
    def losses(self) -> int:
        return self.small_loss + self.big_loss

    @property
    def concentration_ratio(self) -> float:
        """
        0..1, how concentrated are their wins in the top bucket.
        1.0 = pure one-hit wonder (all big wins from >10x bucket).
        0.0 = wins spread across tiers.
        """
        if self.big_wins == 0:
            return 0.0
        return self.above_900 / self.big_wins


@dataclass
class Candidate:
    """
    A smart-money candidate from AVE's /address/smart_wallet/list.
    This carries the full data AVE provides; Phase 2 verification adds
    wallet_info (age) and wallet_tokens (current portfolio).
    """

    address: str
    chain: str

    # AVE's headline numbers
    total_profit_usd: float          # total_profit
    total_profit_rate: float         # total_profit_rate (ROI %)
    token_profit_rate: float         # token_profit_rate (win rate)
    total_volume_usd: float          # total_volume
    total_purchase_usd: float
    total_sold_usd: float

    total_trades: int
    buy_trades: int
    sell_trades: int

    profit_distribution: ProfitDistribution

    last_trade_time: Optional[datetime]
    top_tokens: list[dict]           # tag_items — list of {address, symbol, volume}
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_api(cls, d: dict, chain: str) -> "Candidate":
        return cls(
            address=(d.get("wallet_address") or "").lower(),
            chain=(d.get("chain") or chain).lower(),
            total_profit_usd=_f(d.get("total_profit")),
            total_profit_rate=_f(d.get("total_profit_rate")),
            token_profit_rate=_f(d.get("token_profit_rate")),
            total_volume_usd=_f(d.get("total_volume")),
            total_purchase_usd=_f(d.get("total_purchase")),
            total_sold_usd=_f(d.get("total_sold")),
            total_trades=_i(d.get("total_trades")),
            buy_trades=_i(d.get("buy_trades")),
            sell_trades=_i(d.get("sell_trades")),
            profit_distribution=ProfitDistribution.from_api(d),
            last_trade_time=_parse_time(d.get("last_trade_time")),
            top_tokens=d.get("tag_items") or [],
            raw=d,
        )

    @property
    def days_since_last_trade(self) -> Optional[int]:
        if not self.last_trade_time:
            return None
        now = datetime.now(timezone.utc)
        return max(0, (now - self.last_trade_time).days)


@dataclass
class Holding:
    """One token position in a wallet."""

    token_address: str
    symbol: str
    balance_usd: float
    amount: float
    is_blue_chip: bool = False

    @classmethod
    def from_api(cls, d: dict) -> "Holding":
        return cls(
            token_address=(
                d.get("token")
                or d.get("token_address")
                or d.get("address")
                or ""
            ).lower(),
            symbol=d.get("symbol") or d.get("name") or "?",
            balance_usd=_f(d.get("value_usd") or d.get("balance_usd") or d.get("value")),
            amount=_f(d.get("balance") or d.get("amount")),
            is_blue_chip=bool(d.get("is_blue_chip") or d.get("blue_chip")),
        )


@dataclass
class VerifiedWallet:
    """
    Result of Phase 2 verification.
    Bundles the raw candidate data with portfolio snapshot and our score.
    """

    candidate: Candidate
    age_days: Optional[int]
    portfolio_value_usd: float
    portfolio_size: int
    blue_chip_ratio: float
    holdings: list[Holding]

    score: float = 0.0
    verdict: str = ""        # "APPROVED" | "REVIEW" | "REJECTED"
    reasons: list[str] = field(default_factory=list)

    # Convenience accessors for reporting
    @property
    def address(self) -> str:
        return self.candidate.address

    @property
    def chain(self) -> str:
        return self.candidate.chain

    @property
    def total_profit(self) -> float:
        return self.candidate.total_profit_usd

    @property
    def win_rate(self) -> float:
        return self.candidate.token_profit_rate


@dataclass
class TradeSignal:
    """Detected new/exited position on a watched wallet (Phase 4 monitor)."""

    wallet_address: str
    chain: str
    token_address: str
    token_symbol: str
    action: str  # "OPEN" | "EXIT"
    detected_at: float
    risk_verdict: Optional[str] = None   # "SAFE" | "WARN" | "BLOCK"
    risk_reasons: list[str] = field(default_factory=list)
    suggested_usd: float = 0.0


# ---------- helpers ----------


def _f(v) -> float:
    if v is None or v == "":
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _i(v) -> int:
    if v is None or v == "":
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _parse_time(v) -> Optional[datetime]:
    if not v:
        return None
    try:
        # AVE returns ISO 8601 with Z suffix: "2026-04-15T13:24:31Z"
        s = v.replace("Z", "+00:00") if isinstance(v, str) else v
        return datetime.fromisoformat(s)
    except (ValueError, AttributeError):
        pass
    try:
        return datetime.fromtimestamp(int(v), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None
