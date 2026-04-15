"""
Smoke test for AveClient — run this after setting AVE_API_KEY in .env.
Uses only 3 API calls to stay well within rate limits.

    python scripts/smoke_test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as script from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alphamirror.ave_client import AveClient, AveApiError


def main() -> int:
    try:
        with AveClient() as ave:
            print("[1/3] search('PEPE', chain='bsc') ...")
            results = ave.search("PEPE", chain="bsc", limit=3)
            print(f"  → {len(results)} tokens returned")
            if results:
                sample = results[0]
                print(f"  → first: {_brief(sample)}")

            print("\n[2/3] trending(chain='bsc') ...")
            trending = ave.trending(chain="bsc", page_size=5)
            print(f"  → {len(trending)} trending tokens")

            print("\n[3/3] smart_wallets(chain='bsc') ...")
            smart = ave.smart_wallets(chain="bsc")
            print(f"  → {len(smart)} smart wallets returned")
            if smart:
                print(f"  → first: {_brief(smart[0])}")

        print("\n✓ smoke test passed — AveClient works end-to-end.")
        return 0

    except AveApiError as e:
        print(f"\n✗ API error: {e}", file=sys.stderr)
        print("  Check your AVE_API_KEY and that the free tier is active.", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"\n✗ {e}", file=sys.stderr)
        return 1


def _brief(obj: dict) -> str:
    """Show first few keys of a response for quick eyeball inspection."""
    if not isinstance(obj, dict):
        return str(obj)[:120]
    keys = list(obj.keys())[:6]
    snippet = {k: obj[k] for k in keys}
    return json.dumps(snippet, default=str)[:200]


if __name__ == "__main__":
    sys.exit(main())
