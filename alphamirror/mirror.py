"""
Phase 5: Build self-custody mirror trades.

AlphaMirror is intentionally non-custodial. We don't hold user keys, we don't
run a proxy wallet. Instead we compose the exact AVE Cloud `trade-chain-wallet`
quote command the user would run, and optionally execute it as a subprocess
so the CLI can display the quote inline during the demo.

The user always signs the transaction themselves in their own wallet app.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass
from typing import Optional


# Common stablecoin addresses used as the "in" side for mirror buys.
# Keeps the demo simple — user approves USDT once, then mirrors in USDT.
STABLECOIN_IN = {
    "bsc": "0x55d398326f99059fF775485246999027B3197955",  # USDT (BEP-20)
    "eth": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT (ERC-20)
    "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC (Base)
    "solana": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT (Solana)
}


@dataclass
class MirrorPreview:
    chain: str
    in_token: str
    in_amount_human: float      # e.g. 50.0 (USDT)
    in_amount_wei: int          # e.g. 50 * 10**18 for BSC USDT
    out_token: str
    command: str                # shell command the user can run
    quote_json: Optional[dict] = None  # populated if subprocess executed


def build_mirror_preview(
    chain: str,
    out_token: str,
    in_amount_usd: float,
    in_token: Optional[str] = None,
    decimals: int = 18,
) -> MirrorPreview:
    """
    Compose a `trade-chain-wallet quote` command for a mirror buy.

    Defaults to a stablecoin → target token buy. Amounts are expressed in
    the stablecoin's smallest unit (wei-style). We assume 18 decimals for
    EVM stables unless `decimals` is overridden; for USDC on Ethereum/Base
    pass decimals=6.
    """
    chain = chain.lower()
    stable = in_token or STABLECOIN_IN.get(chain)
    if not stable:
        raise ValueError(f"No default stablecoin configured for chain {chain!r}")

    amount_wei = int(in_amount_usd * (10**decimals))

    # We generate the Docker form — self-contained, doesn't assume the user
    # has the AVE Python package installed. If they do, they can swap out
    # the docker prefix for `python scripts/ave_trade_rest.py`.
    cmd_parts = [
        "docker", "run", "--rm",
        "-e", "AVE_API_KEY=$AVE_API_KEY",
        "-e", "API_PLAN=free",
        "--entrypoint", "python3",
        "ave-cloud", "scripts/ave_trade_rest.py", "quote",
        "--chain", chain,
        "--in-token", stable,
        "--out-token", out_token,
        "--in-amount", str(amount_wei),
        "--swap-type", "buy",
    ]
    command = " ".join(shlex.quote(p) if " " in p else p for p in cmd_parts)

    return MirrorPreview(
        chain=chain,
        in_token=stable,
        in_amount_human=in_amount_usd,
        in_amount_wei=amount_wei,
        out_token=out_token,
        command=command,
    )


def execute_quote_subprocess(
    preview: MirrorPreview,
    timeout: float = 30.0,
) -> MirrorPreview:
    """
    Optionally run the quote command as a subprocess and attach the JSON result.
    Requires the `ave-cloud` Docker image to be built locally. If it's not,
    we return the preview unchanged (command still displayable in UI).
    """
    try:
        result = subprocess.run(
            preview.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0 and result.stdout.strip():
            preview.quote_json = json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
        # Demo-friendly: if Docker isn't set up, we silently fall back to
        # showing the command string. The user can still copy-paste it.
        pass
    return preview
