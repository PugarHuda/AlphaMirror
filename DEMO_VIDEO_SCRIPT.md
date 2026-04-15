# AlphaMirror Demo Video Script (5 minutes)

**Goal:** Convince judges that AlphaMirror solves a real copy-trading pain point
with deep AVE integration and non-custodial design.

**Recording:** Screen recording (OBS / Loom / ShareX) + voiceover. 1080p minimum.
**Delivery:** Upload to YouTube (unlisted) and link in submission form.

---

## Timeline

### 0:00 – 0:30 — Hook (text on screen + voiceover)

**On screen:** Full-screen title card
> "Most 'smart money' wallets you see on Twitter are actually losing money."
> "We prove it with on-chain data."
>
> **AlphaMirror**

**Voiceover:**
> "Copy-trading tools rank wallets by raw profit. That means one lucky 100x
> trade dominates the leaderboard — and you end up mirroring dormant whales
> or one-hit wonders. AlphaMirror is the verification layer AVE Cloud has
> been missing."

---

### 0:30 – 1:00 — The Pitch

**On screen:** GitHub repo README, scroll slowly through the 6-signal table.

**Voiceover:**
> "Built on AVE Cloud Skill, AlphaMirror takes AVE's smart-money candidates
> and stress-tests them against six independent quality signals:
> profitability, consistency, recency, portfolio sanity, volume, and age.
> The output is a 0-to-100 Verification Score with three verdicts — approved,
> review, rejected."

---

### 1:00 – 2:30 — Live Pipeline Run (Streamlit UI)

**Setup before recording:**
```bash
streamlit run app.py
```

**On screen:**
1. Streamlit app loaded with the welcome message
2. In sidebar: select chain `bsc`, candidates `10`
3. Click **Run Pipeline**
4. Show **Phase 1** status box expand briefly
5. Watch **Phase 2** progress bar tick from 1/10 to 10/10

**Voiceover (while progress bar advances):**
> "Phase 1: we call AVE's `smart_wallets` endpoint — their proprietary
> smart-money classifier. Phase 2: for each candidate, we call `wallet_info`
> and `wallet_tokens` to get wallet age and current portfolio. We're on the
> free tier — 1 transaction per second — so this takes about 20 seconds for
> 10 wallets."

---

### 2:30 – 3:30 — Results: The Killer Moment

**On screen:** Results page with ranked wallets. Scroll slowly.
Focus on:
- **Top wallet:** APPROVED, score 92, $123k profit, 75% win rate, 288d age
- **Mid wallet:** REVIEW, score 60, one-hit wonder profile
- **Bottom wallet:** REJECTED, score 40, AVE flagged but -$2k profit over 433 days

**Voiceover:**
> "Out of ten candidates AVE flagged as smart money, only two passed our
> verification. Look at rank six — a hundred and forty-four thousand in
> profit but only twelve percent win rate. That's a one-hit wonder.
> Our scoring catches it.
>
> And rank ten — this wallet has been labeled 'smart money' by AVE for
> four hundred and thirty-three days, but when we actually check the
> numbers, they're down two thousand three hundred forty-four dollars.
> AlphaMirror rejects it. That's the entire product value in one card."

---

### 3:30 – 4:15 — Drill-Down + Self-Custody Mirror

**On screen:** Click the "Details" expander on the top approved wallet.
Show score breakdown, profit-tier bar chart, last-traded badge.

Then click "Mirror a trade from this wallet" → pick a held token →
enter $50 → click "Build self-custody quote".

**Voiceover:**
> "Each score is fully auditable — here's the breakdown, here's the trade
> tier distribution showing the wins are spread across multiple brackets,
> not concentrated in one lucky trade.
>
> And when you're ready to mirror, AlphaMirror composes a self-custody
> trade quote. That's the AVE `trade-chain-wallet quote` command. Copy it,
> run it, sign in your own wallet. AlphaMirror never touches your keys.
> Your custody stays with you."

---

### 4:15 – 4:45 — Technical Proof Points

**On screen:** Side-by-side:
1. Terminal: `python -m alphamirror.cli run --chain bsc --top 5` output
2. README "AVE Cloud Skill Integration" table

**Voiceover:**
> "Under the hood, AlphaMirror uses eleven endpoints across two AVE skills:
> `data-rest` for the analysis, `trade-chain-wallet` for the execution layer.
> All on the free API tier, no whitelist needed. Thread-safe rate limiter,
> offline demo mode for reliable recording, fully type-hinted Python.
> Apache-licensed on GitHub."

---

### 4:45 – 5:00 — Close

**On screen:** Title card again with:
- GitHub URL
- "Built for AVE Claw Hackathon 2026"
- Team name / contact

**Voiceover:**
> "AlphaMirror — verified smart-money copy-trading. Built on AVE Cloud.
> Non-custodial by design. Thanks for watching."

---

## Recording Checklist

- [ ] Streamlit UI loaded with `streamlit run app.py` (not demo mode —
      live data is more impressive)
- [ ] Terminal has `DEMO_MODE=0` and `.env` with a working `AVE_API_KEY`
- [ ] Close all unnecessary apps / browser tabs
- [ ] Dark theme on both Streamlit and terminal for visual consistency
- [ ] Test audio levels with a 10-second sample first
- [ ] Record in one take if possible — rehearse the timeline 2-3 times
- [ ] Export at 1080p, MP4, under 100 MB if uploading anywhere

## If Live API Fails Mid-Recording

Fall back to offline mode and re-record from Phase 1 onwards:

```bash
set DEMO_MODE=1
streamlit run app.py
```

The fixture data in `demo/fixtures.json` produces the same narrative
(1 rejected wallet, 2 approved, visible one-hit wonder pattern).

## Key Talking Points (memorize)

1. **"Eleven endpoints across two AVE skills"** — shows deep integration
2. **"One-hit wonder detector"** — our unique contribution
3. **"Non-custodial by design"** — resonates with Web3 Festival audience
4. **"Ten flagged, two approved, one outright rejected"** — shows the
   verification layer actually matters
5. **"Free tier, no whitelist, no proxy wallet"** — accessibility argument
