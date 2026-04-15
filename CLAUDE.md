# AlphaMirror — AVE Claw Hackathon 2026

Verified smart-money copy-trading agent built on AVE Cloud Skill.
One-liner: *"Copy-trade cuma wallet yang benar-benar profit — bukan yang brand di Twitter."*

## Stack

- **Runtime**: Python 3.13
- **HTTP**: `httpx` (sync, thread-safe rate limiter)
- **UI (optional)**: `streamlit` for demo video
- **AVE Skills used**: `data-rest` (11 endpoints) + `trade-chain-wallet` (quote/build, user signs)
- **API Plan**: `free` — no whitelist, no proxy wallet, no WSS

## Run

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env, put your AVE_API_KEY from https://cloud.ave.ai
python -m alphamirror.cli discover --chain bsc
python -m alphamirror.cli verify --wallet 0xABC... --chain bsc
python -m alphamirror.cli mirror --watch 0xABC... --chain bsc --max-usd 50
# or launch UI
streamlit run app.py
```

## Project Structure

```
alphamirror/
├── ave_client.py       # REST wrapper (base URL, auth, rate limiter, 14 endpoints)
├── models.py           # dataclasses: Candidate, VerifiedWallet, TradeSignal
├── discovery.py        # Phase 1: smart_wallets() → list of candidate wallets
├── verification.py     # Phase 2: wallet_info + wallet_tokens + address_pnl → scored
├── scoring.py          # Verification Score formula (win rate, P&L, age, etc)
├── monitor.py          # Phase 4: poll wallet_tokens diff → detect new positions
├── mirror.py           # Phase 5: chain-wallet quote + build, user signs
└── cli.py              # Orchestrator / entry point
```

## Critical Conventions

1. **Rate limit is hard constraint (1 TPS free tier).** Never batch requests in parallel.
   All calls go through `AveClient._limiter.wait()`. Budget API calls per user action.
2. **Cache aggressively.** Wallet verification results cached 15 min in memory (dict),
   optionally to `.cache/` on disk for demo reliability.
3. **Self-custody by design.** We never ask for private keys. `trade-chain-wallet quote`
   returns unsigned tx; user signs in their own wallet.
4. **No try/except for control flow.** Let errors bubble. `AveApiError` is defined
   only for HTTP status codes. Use conditionals for expected data absence.
5. **Non-obvious comments only.** Code should be self-documenting. Comments explain
   *why*, not *what*. Especially flag rate-limit-sensitive paths.

## AVE API Reference (discovered from source)

Base: `https://data.ave-api.xyz/v2` · Auth header: `X-API-KEY`

| Endpoint | Path | Used in phase |
|---|---|---|
| search | `GET /tokens?keyword=...` | Discovery, resolution |
| token | `GET /tokens/{addr}-{chain}` | Context |
| holders | `GET /tokens/holders/{addr}-{chain}` | Optional enrichment |
| risk | `GET /contracts/{addr}-{chain}` | Safety gate |
| trending | `GET /tokens/trending?chain=...` | Discovery |
| kline | `GET /klines/token/{addr}-{chain}?interval&limit` | Context, monitor |
| txs | `GET /txs/{pair}-{chain}` | Optional |
| smart_wallets | `GET /address/smart_wallet/list?chain=...` | **Phase 1 core** |
| wallet_info | `GET /address/walletinfo?wallet_address&chain` | **Phase 2** |
| wallet_tokens | `GET /address/walletinfo/tokens?wallet_address&chain` | **Phase 2, Phase 4** |
| address_pnl | `GET /address/pnl?wallet_address&chain&token_address` | **Phase 2 core** |
| address_txs | `GET /address/tx?wallet_address&chain` | Phase 2 enrichment |

Chains: `bsc`, `eth`, `base`, `solana`

## Hackathon Context

- **Deadline**: 15 April 2026 (submission window Apr 13–15)
- **Judging**: Innovation 30% / Technical Execution 30% / Real-World Value 40%
- **Track**: Complete Application (Monitoring + Trading Skills)
- **Submission**: GitHub repo + docs + ≤5min demo video
