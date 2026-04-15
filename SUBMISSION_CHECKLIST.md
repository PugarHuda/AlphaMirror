# AlphaMirror — Submission Checklist

Last thing standing between the repo and a submitted entry. **Deadline: 15 April 2026.**

## 1. GitHub Repo

- [ ] Initialize git:
  ```bash
  cd "F:\Hackathons\Hackathon Ave"
  git init
  git add .
  git commit -m "AlphaMirror: verified smart-money copy-trading on AVE Cloud Skill"
  ```
- [ ] Create a **public** repo on GitHub (e.g. `alphamirror`)
- [ ] Push:
  ```bash
  git remote add origin https://github.com/<your-username>/alphamirror.git
  git branch -M main
  git push -u origin main
  ```
- [ ] Confirm `.env` is NOT in the pushed repo (should be gitignored)
- [ ] Confirm `.venv/` is NOT in the pushed repo
- [ ] Add a descriptive repo description + topics: `ave-cloud`, `defi`, `ai-agent`,
  `copy-trading`, `web3`, `bsc`

## 2. Demo Video

- [ ] Read `DEMO_VIDEO_SCRIPT.md` end-to-end
- [ ] Rehearse the 5-minute timeline 2-3 times with the Streamlit UI
- [ ] Run `streamlit run app.py` and confirm the pipeline succeeds **live** on BSC
- [ ] If live API flakes during recording, fall back to `DEMO_MODE=1`
- [ ] Record at 1080p minimum with clear audio
- [ ] Keep under 5 minutes (hackathon rule)
- [ ] Upload to YouTube as **Unlisted** (not private — judges need the link)
- [ ] Copy the video URL

## 3. Project Documentation

Already present in the repo:

- [x] `README.md` — judges' entry point
- [x] `CLAUDE.md` — internal dev docs (optional to keep)
- [x] `DEMO_VIDEO_SCRIPT.md` — video production script
- [x] `SUBMISSION_CHECKLIST.md` — this file

Add before submission (optional but helpful):

- [ ] `LICENSE` file — MIT recommended, matches AVE Cloud Skill's license
- [ ] `screenshots/` folder with 3-4 PNGs of the Streamlit UI
- [ ] A link to the demo video in the README header

Quick add:

```bash
# MIT License
curl -o LICENSE https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt
# Replace [year] and [fullname] in LICENSE
```

## 4. Submission Form

Per the hackathon rules, submit via the **official submission channel**
(check the TG group `t.me/+62d86Wq3ogs5YTU1` for the exact URL — it's not
on the public landing page).

You will need:

- [ ] **Team name** and **leader name** (same as registration)
- [ ] **GitHub repo URL** (public)
- [ ] **Demo video URL** (YouTube unlisted)
- [ ] **Project description** — use this 2-paragraph version:

> **AlphaMirror** is a verified smart-money copy-trading agent built on
> AVE Cloud Skill. While most copy-trading tools rank wallets by raw P&L,
> AlphaMirror takes AVE's `smart_wallets` classifier as a candidate pool
> and stress-tests each wallet against six independent quality signals:
> profitability, consistency (detecting one-hit wonders via AVE's
> profit-tier distribution), recency, portfolio sanity, trading volume,
> and wallet age. The output is a 0–100 Verification Score with three
> verdicts — APPROVED, REVIEW, REJECTED — with full score breakdowns.
>
> AlphaMirror is **non-custodial by design**. Mirror trades are built as
> self-custody `trade-chain-wallet quote` commands that the user signs in
> their own wallet app — we never touch private keys. The project uses
> **11 endpoints across 2 AVE skills** on the free tier, with a thread-safe
> client-side rate limiter (1 TPS) and an offline fixture mode for
> reliable demo recording.

- [ ] **Track**: Complete Application (monitoring + trading skills combined)
- [ ] **Tech stack**: Python 3.13, httpx, Streamlit, AVE Cloud Skill

## 5. Final Pre-Submit Smoke Test

Run this sequence from a fresh terminal with `AVE_API_KEY` set:

```bash
cd "F:\Hackathons\Hackathon Ave"
python -m alphamirror.cli discover --chain bsc --top 5
python -m alphamirror.cli run --chain bsc --top 5
python -m alphamirror.cli mirror --chain bsc --token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c --usd 50
python -m streamlit run app.py  # visually confirm the UI
```

All four should complete without errors. If `run` shows at least one
REJECTED verdict in the output, your demo narrative is ready.

## 6. After Submission

- [ ] Post confirmation in TG group
- [ ] Pin the demo video URL somewhere you can easily find it
- [ ] Prepare a short "what we'd build next" note in case of follow-up
  questions from judges during evaluation (Apr 16-17)
- [ ] Optional: publish a Twitter/X post with the demo video link and
  `@aveai_info` tag for bonus market exposure (judging rubric mentions
  "Real-World Value 40%" and visible traction helps)

## Good Luck

The project is functional, the pipeline is deep, the narrative is clear.
Ship it.
