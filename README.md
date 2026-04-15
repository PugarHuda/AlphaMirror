# AlphaMirror

**Verified smart-money copy-trading — built on [AVE Cloud Skill](https://github.com/AveCloud/ave-cloud-skill).**

> Most "smart money" wallets you see on Twitter are actually unprofitable.
> AlphaMirror verifies them with on-chain data before you ever copy a trade.

---

## The Problem

Copy-trading platforms rank wallets by raw P&L. That means:

- One lucky 100x trade dominates the leaderboard
- Dormant whales look like active alpha hunters
- A wallet with 29 trades and 2 big wins gets conflated with one that has 8,685 trades and zero big wins
- Retail follows the label and gets rekt

AVE Cloud's `smart_wallets` endpoint already classifies promising wallets —
but a label is not the same as a verdict. AlphaMirror is the **verification
layer** that turns AVE's smart-money candidate pool into a **ranked, scored,
audit-trailed list** you can actually mirror.

## The Solution

AlphaMirror runs a 5-phase pipeline on top of AVE Cloud's `data-rest` and
`trade-chain-wallet` skills:

| Phase | What it does | AVE skill used |
|---|---|---|
| 1. **Discover** | Pull candidate smart wallets from AVE's classifier | `smart_wallets` |
| 2. **Verify** | Score each candidate against 6 independent quality signals | `wallet_info`, `wallet_tokens` |
| 3. **Rank** | Sort by our Verification Score (0–100) with APPROVED / REVIEW / REJECTED verdicts | — |
| 4. **Monitor** | Poll approved wallets for new positions, with per-token risk gate | `wallet_tokens` (diff), `risk` |
| 5. **Mirror** | Build a self-custody quote — user signs in their own wallet | `trade-chain-wallet quote` |

**You never give us your private keys.** AlphaMirror is non-custodial by design.

## Verification Score Breakdown

The Verification Score (0–100) is a weighted combination of six signals that
cross-check AVE's classification:

| Weight | Signal | What it catches |
|---:|---|---|
| 25 | **Profitability** | Is `total_profit` genuinely positive? |
| 25 | **Consistency** | Are wins spread across tiers, or is it a one-hit wonder? |
| 15 | **Recency** | Still trading, or dormant smart money? |
| 15 | **Portfolio** | Rational mix of blue chips and alpha, or empty after rotation? |
| 10 | **Volume** | Real serious wallet, or low-volume tester? |
| 10 | **Age** | Old enough to survive anti-sybil? |

Thresholds:
- **APPROVED** (≥70) — mirror-worthy
- **REVIEW** (40–69) — we show the data, you decide
- **REJECTED** (<40) — AVE flagged it, we don't agree

The **one-hit-wonder detector** is the most distinctive piece: it uses AVE's
per-tier profit distribution (how many trades returned 10x+, 3-5x, 2-4x,
etc.) to penalize wallets whose profits came from a single lucky bet.

## AVE Cloud Skill Integration

AlphaMirror uses **12 endpoints across 2 skills**, all on the free API tier:

### `data-rest` skill (11 endpoints)

| Endpoint | Used for |
|---|---|
| `smart_wallets` | Phase 1 discovery — AVE's built-in smart-money classifier |
| `wallet_info` | Wallet age / anti-sybil check |
| `wallet_tokens` | Current portfolio snapshot + polling diff |
| `address_pnl` | Per-token P&L drill-down in wallet detail modal |
| `address_txs` | Wallet activity history in drill-down view |
| `search` | Token resolution by symbol in monitor page |
| `token` | Token metadata in drill-down modal |
| `kline_token` | 48h price chart visualization in token modal |
| `risk` | Honeypot / tax / owner-permissions safety gate |
| `trending` | Live trending tokens discovery on monitor page |
| `holders` | Top holder distribution in token analysis |
| `txs` | Recent swap transactions in token modal |

### `trade-chain-wallet` skill (1 endpoint)

| Endpoint | Used for |
|---|---|
| `quote` | Build self-custody mirror trade previews |

## Running It

Requires Python 3.10+ and an AVE Cloud API key (free tier — get one at
[cloud.ave.ai](https://cloud.ave.ai)).

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# edit .env and paste your AVE_API_KEY

# 3. Run the full pipeline from CLI
python -m alphamirror.cli run --chain bsc --top 5

# 4. Or launch the Streamlit UI for the demo video look
streamlit run app.py

# 5. Or run the FastAPI backend + Next.js frontend (full integration)
python server.py  # backend on port 8000
cd frontend && npm install && npm run build && npm start  # frontend on port 3000
```

### Next.js Frontend

The `frontend/` directory contains a production-ready Next.js 14 application that
demonstrates **all 12 AVE endpoints** in action:

- **Landing page** (`/`) — Hero, features, endpoint showcase
- **Dashboard** (`/dashboard`) — Full verification pipeline with drill-down modals
  - Wallet detail modal uses `address_pnl` and `address_txs` for deep analysis
  - Token detail modal uses `token`, `kline_token`, `holders`, `txs`, and `risk`
- **Monitor** (`/monitor`) — Live polling + trending tokens discovery

The frontend proxies `/api/*` requests to the FastAPI backend at `http://127.0.0.1:8000`.

### CLI subcommands

```bash
# List raw smart-money candidates (1 API call)
python -m alphamirror.cli discover --chain bsc --top 10

# Full pipeline: discover + verify + rank
python -m alphamirror.cli run --chain bsc --top 5

# Verify a specific wallet (must be in current smart-wallet pool)
python -m alphamirror.cli verify --wallet 0x... --chain bsc

# Build a self-custody mirror trade preview
python -m alphamirror.cli mirror --chain bsc \
    --token 0x... --usd 50

# Watch wallets for new positions (Phase 4)
python -m alphamirror.cli watch --wallet 0x... --chain bsc \
    --interval 60 --iterations 3
```

### Offline demo mode

For recording a reliable demo video (or developing without hitting the API),
set `DEMO_MODE=1` — the entire pipeline switches to `MockAveClient` which
serves canned fixtures from `demo/fixtures.json`.

```bash
DEMO_MODE=1 python -m alphamirror.cli run --chain bsc --top 5
DEMO_MODE=1 streamlit run app.py
```

The mock client simulates the 1-TPS free-tier latency so the demo paces
exactly like the live pipeline.

## Architecture

```
alphamirror/
├── ave_client.py       AVE REST wrapper (14 endpoints, rate limiter, auth)
├── mock_client.py      Offline fixture-backed client (DEMO_MODE=1)
├── client_factory.py   Live vs mock selection
├── models.py           Typed data classes (Candidate, VerifiedWallet, ...)
├── discovery.py        Phase 1 — smart_wallets fetch
├── verification.py     Phase 2 — wallet_info + wallet_tokens verification
├── scoring.py          Verification Score formula (6 signals, weighted)
├── monitor.py          Phase 4 — poll + diff + risk gate
├── mirror.py           Phase 5 — self-custody quote builder
└── cli.py              Orchestrator with rich terminal output
```

### Rate limiting

AVE's free tier is **1 TPS**. AlphaMirror enforces this client-side via
a thread-safe `_RateLimiter` in `ave_client.py`, so concurrent UI threads
don't race into 429s. All calls serialize through a single lock.

### Why this works on free tier

Early versions of this design called `address_pnl` 5× per candidate to
reconstruct profitability from holdings — too expensive at 1 TPS. The
current design delegates that computation to AVE's `smart_wallets`
endpoint (which already returns `total_profit`, `token_profit_rate`,
and the profit-tier distribution) and uses `wallet_info` +
`wallet_tokens` purely as independent cross-checks. The result: **2 API
calls per verified wallet**, ~6s for a top-3 run end-to-end.

## Hackathon Track

This project targets the **Complete Application** track of the AVE Claw
Hackathon 2026. It integrates:

- **Monitoring Skill** — Phase 4 (`watch`) polls tracked wallets and
  triggers alerts on new positions with an automatic risk gate.
- **Trading Skill** — Phase 5 (`mirror`) composes self-custody trades
  via `trade-chain-wallet quote`, ready for the user to sign.

### Judging Dimensions Addressed

- **Innovation (30%)** — Verification-layer approach is novel. No prior
  smart-money tool we can find uses the per-tier profit distribution to
  detect one-hit wonders.
- **Technical Execution (30%)** — 11 endpoints, 2 skills, deep
  integration, rate-limit-aware architecture, offline demo mode, full
  type-hinted Python.
- **Real-World Value (40%)** — Copy-trading is a multi-billion-dollar
  retail market, and AlphaMirror directly solves the "which wallets
  should I trust" problem with a defensible methodology.

## License

MIT

## Acknowledgements

- [AVE Cloud](https://cloud.ave.ai) for the skill toolkit and free tier
- [AVE Cloud Skill](https://github.com/AveCloud/ave-cloud-skill) for the
  Python client source we drew REST shapes from
