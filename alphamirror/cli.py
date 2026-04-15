"""
AlphaMirror CLI — orchestrate the full pipeline from the terminal.

Subcommands:
    discover   List smart-money candidates on a chain (1 API call)
    verify     Verify a list of candidates with full scoring (~7 calls/wallet)
    run        Discover → verify → show top-N report (end-to-end)
    mirror     Print a self-custody mirror trade command for a token
    watch      Poll tracked wallets for new positions (blocking)

Usage:
    python -m alphamirror.cli discover --chain bsc
    python -m alphamirror.cli run --chain bsc --top 5
    python -m alphamirror.cli mirror --chain bsc --token 0x... --usd 50
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from rich.console import Console
from rich.table import Table

from .ave_client import AveApiError
from .client_factory import make_client
from .discovery import discover_candidates
from .mirror import build_mirror_preview, execute_quote_subprocess
from .monitor import MAX_WALLETS_FREE, watch_loop
from .verification import verify_all, verify_one
from .models import Candidate, TradeSignal


console = Console()


# ---------- subcommand: discover ----------


def cmd_discover(args) -> int:
    with make_client() as ave:
        candidates = discover_candidates(
            ave, chain=args.chain, keyword=args.keyword, max_candidates=args.top
        )
    if not candidates:
        console.print("[yellow]No smart wallets returned.[/yellow]")
        return 1

    table = Table(title=f"Smart Money Candidates — {args.chain.upper()}")
    table.add_column("#", style="dim")
    table.add_column("Wallet")
    table.add_column("Total P&L", justify="right")
    table.add_column("ROI", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("Trades", justify="right")
    table.add_column("Big Wins", justify="right")
    table.add_column("Last Trade", justify="right")
    for i, c in enumerate(candidates, start=1):
        days = c.days_since_last_trade
        last_str = f"{days}d ago" if days is not None else "-"
        table.add_row(
            str(i),
            c.address,
            _fmt_usd(c.total_profit_usd),
            _fmt_pct(c.total_profit_rate),
            _fmt_pct(c.token_profit_rate),
            str(c.total_trades),
            str(c.profit_distribution.big_wins),
            last_str,
        )
    console.print(table)
    console.print(
        f"\n[dim]Raw AVE classification — not yet verified. "
        f"Run `verify --wallet <addr> --chain {args.chain}` to score.[/dim]"
    )
    return 0


# ---------- subcommand: verify ----------


def cmd_verify(args) -> int:
    """
    Verify a wallet by first fetching its full candidate data from the
    smart_wallets endpoint (so we have total_profit, win rate, etc.) then
    running the verification layer. If the wallet isn't in AVE's smart
    wallet list, we fall back to a minimal candidate with zeros.
    """
    target = args.wallet.lower()
    with make_client() as ave:
        console.print(f"[dim]Looking up {target} in smart wallet list...[/dim]")
        pool = ave.smart_wallets(chain=args.chain)
        match = next(
            (Candidate.from_api(r, chain=args.chain)
             for r in pool
             if (r.get("wallet_address") or "").lower() == target),
            None,
        )
        if match is None:
            console.print(
                "[yellow]Wallet not in AVE's smart wallet pool on this chain. "
                "Proceeding with zero-baseline verification.[/yellow]"
            )
            match = Candidate.from_api({"wallet_address": target, "chain": args.chain}, args.chain)

        console.print(f"[bold]Verifying {match.address}...[/bold]")
        verified = verify_one(
            ave,
            match,
            on_progress=lambda m: console.print(f"[dim]{m}[/dim]"),
        )
    _print_verdict(verified)
    return 0 if verified.verdict != "REJECTED" else 2


# ---------- subcommand: run (discover + verify + report) ----------


def cmd_run(args) -> int:
    with make_client() as ave:
        console.print(f"[bold]Phase 1:[/bold] discovering candidates on {args.chain}...")
        candidates = discover_candidates(
            ave, chain=args.chain, keyword=args.keyword, max_candidates=args.top
        )
        if not candidates:
            console.print("[red]No candidates returned.[/red]")
            return 1
        console.print(f"  -> {len(candidates)} candidates")

        console.print(f"\n[bold]Phase 2:[/bold] verifying (~{len(candidates) * 2}s)...")
        verified = verify_all(
            ave,
            candidates,
            on_progress=lambda m: console.print(f"[dim]{m}[/dim]"),
        )

    table = Table(title=f"Verified Smart Money — {args.chain.upper()}")
    table.add_column("Rank", style="dim")
    table.add_column("Wallet")
    table.add_column("Score", justify="right")
    table.add_column("Verdict")
    table.add_column("Total P&L", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("Portfolio", justify="right")
    table.add_column("Age", justify="right")
    for i, v in enumerate(verified, start=1):
        table.add_row(
            str(i),
            v.address,
            f"{v.score:.0f}",
            _style_verdict(v.verdict),
            _fmt_usd(v.total_profit),
            _fmt_pct(v.win_rate),
            _fmt_usd(v.portfolio_value_usd),
            f"{v.age_days}d" if v.age_days else "-",
        )
    console.print(table)

    approved = [v for v in verified if v.verdict == "APPROVED"]
    rejected = [v for v in verified if v.verdict == "REJECTED"]
    console.print(
        f"\n[green]{len(approved)} APPROVED[/green] · "
        f"[red]{len(rejected)} REJECTED[/red] "
        f"([dim]AVE flagged these as smart money but our verification "
        f"says otherwise[/dim])"
    )
    return 0


# ---------- subcommand: mirror ----------


def cmd_mirror(args) -> int:
    preview = build_mirror_preview(
        chain=args.chain,
        out_token=args.token,
        in_amount_usd=args.usd,
        decimals=args.decimals,
    )
    if args.execute:
        preview = execute_quote_subprocess(preview)

    console.print(f"\n[bold]Mirror Trade Preview[/bold]")
    console.print(f"  chain:       [cyan]{preview.chain}[/cyan]")
    console.print(f"  in:          [cyan]${preview.in_amount_human:.2f}[/cyan] "
                  f"({preview.in_token[:10]}...)")
    console.print(f"  out:         [cyan]{preview.out_token}[/cyan]")
    console.print(f"\n[dim]# Quote command (self-custody — you sign):[/dim]")
    console.print(f"[white]{preview.command}[/white]")

    if preview.quote_json:
        console.print(f"\n[bold]Live Quote:[/bold]")
        console.print(preview.quote_json)
    else:
        console.print(
            "\n[dim](Run with --execute to invoke the AVE Docker quote command "
            "inline, or copy/paste the command above.)[/dim]"
        )
    return 0


# ---------- subcommand: watch ----------


def cmd_watch(args) -> int:
    wallets = [(w.lower(), args.chain) for w in args.wallet]
    if len(wallets) > MAX_WALLETS_FREE:
        console.print(
            f"[red]free tier limits to {MAX_WALLETS_FREE} tracked wallets[/red]"
        )
        return 1

    def on_signal(sig: TradeSignal) -> None:
        tag = {"OPEN": "[green]OPEN[/green]", "EXIT": "[yellow]EXIT[/yellow]"}.get(
            sig.action, sig.action
        )
        console.print(
            f"{tag} wallet=[cyan]{sig.wallet_address[:10]}...[/cyan] "
            f"token=[cyan]{sig.token_symbol}[/cyan] "
            f"risk=[magenta]{sig.risk_verdict or '-'}[/magenta]"
        )
        if sig.risk_reasons:
            console.print(f"  [dim]-> {'; '.join(sig.risk_reasons)}[/dim]")

    console.print(
        f"[bold]Watching {len(wallets)} wallet(s) on {args.chain}[/bold] "
        f"(poll every {args.interval}s, Ctrl+C to stop)"
    )
    with make_client() as ave:
        try:
            watch_loop(
                ave,
                wallets,
                on_signal=on_signal,
                interval_sec=args.interval,
                max_iterations=args.iterations,
            )
        except KeyboardInterrupt:
            console.print("\n[dim]stopped[/dim]")
    return 0


# ---------- formatters ----------


def _fmt_usd(v: Optional[float]) -> str:
    if v is None:
        return "-"
    sign = "+" if v > 0 else ""
    color = "green" if v > 0 else "red" if v < 0 else "white"
    return f"[{color}]{sign}${v:,.0f}[/{color}]"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "-"
    if 0 <= v <= 1:
        v = v * 100
    return f"{v:.0f}%"


def _style_verdict(v: str) -> str:
    return {
        "APPROVED": "[green]APPROVED[/green]",
        "REVIEW": "[yellow]REVIEW[/yellow]",
        "REJECTED": "[red]REJECTED[/red]",
    }.get(v, v)


def _print_verdict(v) -> None:
    c = v.candidate
    pd = c.profit_distribution
    console.print(f"\n[bold]{v.address}[/bold]")
    console.print(f"  verdict:     {_style_verdict(v.verdict)}")
    console.print(f"  score:       [bold]{v.score}/100[/bold]")
    console.print(f"  total P&L:   {_fmt_usd(c.total_profit_usd)} "
                  f"(ROI {_fmt_pct(c.total_profit_rate)})")
    console.print(f"  win rate:    {_fmt_pct(c.token_profit_rate)}")
    console.print(f"  trades:      {c.total_trades} "
                  f"({c.buy_trades} buy / {c.sell_trades} sell)")
    console.print(f"  volume:      {_fmt_usd(c.total_volume_usd)}")
    days = c.days_since_last_trade
    console.print(f"  last trade:  {days}d ago" if days is not None else "  last trade:  unknown")
    console.print(f"  portfolio:   {_fmt_usd(v.portfolio_value_usd)} "
                  f"({v.portfolio_size} positions, {_fmt_pct(v.blue_chip_ratio)} blue chip)")
    console.print(f"  age:         {v.age_days}d" if v.age_days else "  age:         unknown")
    console.print("\n[bold]Trade profit distribution:[/bold]")
    console.print(f"  >10x wins:   {pd.above_900}")
    console.print(f"  5-10x wins:  {pd.p500_900}")
    console.print(f"  3-5x wins:   {pd.p300_500}")
    console.print(f"  2-4x wins:   {pd.p100_300}")
    console.print(f"  1.1-2x wins: {pd.p10_100}")
    console.print(f"  flat:        {pd.flat}")
    console.print(f"  small loss:  {pd.small_loss}")
    console.print(f"  big loss:    {pd.big_loss}")
    console.print("\n[bold]Score breakdown:[/bold]")
    for reason in v.reasons:
        console.print(f"  · {reason}")


# ---------- argparse ----------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="alphamirror")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="list smart money candidates")
    d.add_argument("--chain", required=True)
    d.add_argument("--keyword", default=None)
    d.add_argument("--top", type=int, default=10)
    d.set_defaults(fn=cmd_discover)

    v = sub.add_parser("verify", help="verify a single wallet")
    v.add_argument("--wallet", required=True)
    v.add_argument("--chain", required=True)
    v.add_argument("--sample", type=int, default=5)
    v.set_defaults(fn=cmd_verify)

    r = sub.add_parser("run", help="discover + verify + report")
    r.add_argument("--chain", required=True)
    r.add_argument("--keyword", default=None)
    r.add_argument("--top", type=int, default=5)
    r.add_argument("--sample", type=int, default=5)
    r.set_defaults(fn=cmd_run)

    m = sub.add_parser("mirror", help="build a self-custody mirror trade")
    m.add_argument("--chain", required=True)
    m.add_argument("--token", required=True, help="target token contract address")
    m.add_argument("--usd", type=float, default=50.0)
    m.add_argument("--decimals", type=int, default=18,
                   help="stablecoin decimals (18 for BSC USDT, 6 for ETH USDC)")
    m.add_argument("--execute", action="store_true",
                   help="run the quote command via Docker subprocess")
    m.set_defaults(fn=cmd_mirror)

    w = sub.add_parser("watch", help="poll wallets for new positions")
    w.add_argument("--wallet", action="append", required=True,
                   help="wallet address (repeat for multiple)")
    w.add_argument("--chain", required=True)
    w.add_argument("--interval", type=int, default=60)
    w.add_argument("--iterations", type=int, default=None,
                   help="stop after N polls (for demo/testing)")
    w.set_defaults(fn=cmd_watch)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except AveApiError as e:
        console.print(f"[red]AVE API error: {e}[/red]")
        return 1
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
