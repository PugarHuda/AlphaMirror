"""
Phase 4: Monitor verified wallets for new positions.

We poll `wallet_tokens` for each tracked wallet on an interval and compute
a diff against the previous snapshot. A new token address in the current
holdings = OPEN signal, worth mirroring.

This is explicitly polling-based (not WebSocket) because AVE's WSS feed
requires the `pro` plan. On free tier (1 TPS) we can realistically poll
3-5 wallets at 60-second intervals.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from .ave_client import AveClient, AveApiError
from .models import Holding, TradeSignal


# Default safe polling parameters for free tier (1 TPS).
#   interval = 60s → budget 1 wallet_tokens call per wallet per minute
#   3 wallets = 3/min → well within 60 TPM tolerance
DEFAULT_POLL_INTERVAL_SEC = 60
MAX_WALLETS_FREE = 3


@dataclass
class WalletState:
    """In-memory state for a tracked wallet: set of current token addresses."""

    address: str
    chain: str
    holdings: dict[str, Holding]  # token_address → Holding
    last_polled: float = 0.0

    @classmethod
    def from_holdings(cls, address: str, chain: str, holdings: list[Holding]) -> "WalletState":
        return cls(
            address=address,
            chain=chain,
            holdings={h.token_address: h for h in holdings if h.token_address},
            last_polled=time.time(),
        )


SignalHandler = Callable[[TradeSignal], None]


def take_snapshot(ave: AveClient, wallet: str, chain: str) -> WalletState:
    """Fetch current holdings for a wallet and wrap as a WalletState."""
    raw = ave.wallet_tokens(wallet, chain, hide_sold=True) or []
    holdings = [Holding.from_api(r) for r in raw]
    return WalletState.from_holdings(wallet, chain, holdings)


def diff_and_alert(
    ave: AveClient,
    prev: WalletState,
    on_signal: SignalHandler,
) -> WalletState:
    """
    Poll the wallet, compare with previous state, and fire TradeSignals
    for any newly-opened positions. Returns the new state.

    A "new position" = token address that wasn't in prev.holdings.
    Exits (token disappeared) are also emitted but without risk check.
    """
    new_state = take_snapshot(ave, prev.address, prev.chain)

    prev_tokens = set(prev.holdings.keys())
    curr_tokens = set(new_state.holdings.keys())

    opened = curr_tokens - prev_tokens
    exited = prev_tokens - curr_tokens

    for token in opened:
        h = new_state.holdings[token]
        signal = TradeSignal(
            wallet_address=prev.address,
            chain=prev.chain,
            token_address=token,
            token_symbol=h.symbol,
            action="OPEN",
            detected_at=time.time(),
        )
        # Enrich with risk check (extra 1 call — worth it)
        _attach_risk(ave, signal)
        on_signal(signal)

    for token in exited:
        h = prev.holdings[token]
        signal = TradeSignal(
            wallet_address=prev.address,
            chain=prev.chain,
            token_address=token,
            token_symbol=h.symbol,
            action="EXIT",
            detected_at=time.time(),
        )
        on_signal(signal)

    return new_state


def _attach_risk(ave: AveClient, signal: TradeSignal) -> None:
    """Run AVE's risk check on the newly-opened token and annotate the signal."""
    try:
        risk = ave.risk(signal.token_address, signal.chain)
    except AveApiError:
        signal.risk_verdict = "UNKNOWN"
        return

    if not isinstance(risk, dict):
        signal.risk_verdict = "UNKNOWN"
        return

    reasons: list[str] = []
    block = False

    # These field names are defensive — the actual AVE contract response
    # may vary. We check multiple common keys.
    if _flag(risk, ("is_honeypot", "honeypot")):
        reasons.append("honeypot detected")
        block = True

    buy_tax = _num(risk, ("buy_tax", "buy_fee"))
    sell_tax = _num(risk, ("sell_tax", "sell_fee"))
    if buy_tax is not None and buy_tax > 10:
        reasons.append(f"buy tax {buy_tax}%")
        block = True
    if sell_tax is not None and sell_tax > 10:
        reasons.append(f"sell tax {sell_tax}%")
        block = True

    if _flag(risk, ("can_take_back_ownership", "owner_can_mint")):
        reasons.append("owner retains dangerous control")
        block = True

    signal.risk_verdict = "BLOCK" if block else ("WARN" if reasons else "SAFE")
    signal.risk_reasons = reasons


def _flag(d: dict, keys: Iterable[str]) -> bool:
    for k in keys:
        v = d.get(k)
        if v in (True, 1, "1", "true", "yes"):
            return True
    return False


def _num(d: dict, keys: Iterable[str]) -> Optional[float]:
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def watch_loop(
    ave: AveClient,
    wallets: list[tuple[str, str]],  # list of (address, chain)
    on_signal: SignalHandler,
    interval_sec: int = DEFAULT_POLL_INTERVAL_SEC,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Blocking poll loop. Use `max_iterations=N` for demo / testing.
    Caller handles signals via the on_signal callback.
    """
    if len(wallets) > MAX_WALLETS_FREE:
        raise ValueError(
            f"free tier supports at most {MAX_WALLETS_FREE} tracked wallets "
            f"(requested {len(wallets)})"
        )

    states = {
        addr: take_snapshot(ave, addr, chain) for addr, chain in wallets
    }

    i = 0
    while True:
        time.sleep(interval_sec)
        for addr, _ in wallets:
            states[addr] = diff_and_alert(ave, states[addr], on_signal)
        i += 1
        if max_iterations is not None and i >= max_iterations:
            return
