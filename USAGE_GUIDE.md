# AlphaMirror — Usage Guide

Panduan lengkap menjalankan AlphaMirror: dari setup pertama kali, CLI subcommands,
Streamlit UI, hingga troubleshooting. Semua command siap copy-paste.

---

## 1. Quick Start (3 menit)

```bash
# Clone atau masuk ke folder project
cd "F:\Hackathons\Hackathon Ave"

# Install deps (sekali saja)
pip install -r requirements.txt

# Setup API key
copy .env.example .env
# Edit .env → paste AVE_API_KEY dari https://cloud.ave.ai

# Smoke test (3 API calls, ~3 detik)
python scripts/smoke_test.py

# Full pipeline (hasil paling menarik untuk demo)
python -m alphamirror.cli run --chain bsc --top 5
```

Kalau smoke test menampilkan `[PASS] smoke test passed`, semua siap.

---

## 2. CLI Commands — Cheat Sheet

AlphaMirror punya 5 subcommand. Semua dimulai dengan `python -m alphamirror.cli`.

### 2.1 `discover` — List Smart Money Candidates (1 API call)

Tampilkan daftar wallet yang AVE klasifikasikan sebagai smart money di suatu chain.
**Ini belum di-verify** — data mentah dari AVE.

```bash
# Default: BSC, top 10
python -m alphamirror.cli discover --chain bsc --top 10

# Chain lain
python -m alphamirror.cli discover --chain eth --top 5
python -m alphamirror.cli discover --chain base --top 5
python -m alphamirror.cli discover --chain solana --top 5

# Filter by keyword (cari wallet yang trade token tertentu)
python -m alphamirror.cli discover --chain bsc --keyword PEPE --top 5
```

**Output:** Tabel dengan wallet address, total P&L, ROI, win rate, jumlah trade,
big wins count, last trade.

**Use case:** Quick look untuk lihat siapa aja yang AVE anggap smart money sekarang.

---

### 2.2 `verify` — Deep Score Satu Wallet

Verifikasi lengkap (Phase 1 lookup + Phase 2 cross-check + scoring) untuk
**satu wallet spesifik**.

```bash
# Wallet harus masih ada di current smart_wallets pool AVE
python -m alphamirror.cli verify --wallet 0x4b9c0f2e8d3a5f7c1b2d8e4f6a9c5d3b1e2f4a6c --chain bsc

# Chain lain
python -m alphamirror.cli verify --wallet 0xABCDEF... --chain eth
```

**Output:** Full score breakdown dengan 6 signals, trade profit distribution,
dan verdict APPROVED / REVIEW / REJECTED.

**Limitation:** Kalau wallet-nya tidak di current top-100 smart_wallets pool,
command fallback ke zero-baseline (REJECTED). Pakai `run` kalau mau auto-discover.

---

### 2.3 `run` — Full Pipeline (RECOMMENDED untuk demo)

Discover + verify + rank + report dalam satu command. **Ini yang dipakai di
demo video.**

```bash
# Standard demo run
python -m alphamirror.cli run --chain bsc --top 5

# Lebih banyak wallet (akan lebih lama karena 1 TPS rate limit)
python -m alphamirror.cli run --chain bsc --top 10

# Chain lain
python -m alphamirror.cli run --chain eth --top 5
```

**Output:** Ranked table dengan 5 kolom (Rank, Score, Verdict, P&L, Win Rate,
Portfolio, Age) + summary verdict counts.

**Rate limit budget:**
- `--top 5`: ~12 detik (1 + 5×2 + buffer)
- `--top 10`: ~22 detik
- `--top 15`: ~32 detik

**Narrative yang biasanya muncul:**
- 1-3 APPROVED (score ≥70)
- 2-6 REVIEW (score 40-69)
- 0-2 REJECTED (score <40) — the killer moment untuk demo

---

### 2.4 `mirror` — Build Self-Custody Trade Preview

Generate exact `trade-chain-wallet quote` command untuk mirror trade.
**Tidak execute apapun** — cuma compose command yang user bisa run sendiri
dan sign di wallet-nya.

```bash
# Basic: 50 USDT → target token di BSC
python -m alphamirror.cli mirror \
    --chain bsc \
    --token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
    --usd 50

# Ukuran berbeda
python -m alphamirror.cli mirror --chain bsc --token 0xABC... --usd 100

# Ethereum dengan USDC (6 decimals)
python -m alphamirror.cli mirror \
    --chain eth \
    --token 0x6982508145454Ce325dDbE47a25d4ec3d2311933 \
    --usd 25 \
    --decimals 6

# Base
python -m alphamirror.cli mirror --chain base --token 0x... --usd 30 --decimals 6

# Execute inline (butuh Docker + ave-cloud image)
python -m alphamirror.cli mirror --chain bsc --token 0x... --usd 50 --execute
```

**Output:** Pretty-printed summary + full `docker run` command yang user
copy-paste. Dengan `--execute`, otomatis run command dan tampilkan quote JSON.

---

### 2.5 `watch` — Poll Wallets for New Positions

Phase 4: monitor beberapa wallet approved, detect new positions secara
real-time (polling-based, bukan WSS).

```bash
# Watch 1 wallet, 60 detik interval, jalan terus sampai Ctrl+C
python -m alphamirror.cli watch \
    --wallet 0x4b9c0f2e8d3a5f7c1b2d8e4f6a9c5d3b1e2f4a6c \
    --chain bsc

# Watch beberapa wallet (max 3 di free tier)
python -m alphamirror.cli watch \
    --wallet 0xAAA... \
    --wallet 0xBBB... \
    --chain bsc \
    --interval 60

# Test mode: 1 iterasi saja (untuk demo video)
python -m alphamirror.cli watch \
    --wallet 0x... \
    --chain bsc \
    --interval 10 \
    --iterations 1

# Short interval untuk demo live (tidak recommended production)
python -m alphamirror.cli watch \
    --wallet 0x... \
    --chain bsc \
    --interval 30 \
    --iterations 3
```

**Output:** Saat ada position change, log `OPEN` / `EXIT` dengan risk verdict
dan reasons kalau ada red flag.

---

## 3. Streamlit UI — Visual Demo

Launch interactive UI untuk demo video atau exploration:

```bash
python -m streamlit run app.py
```

Browser otomatis buka `http://localhost:8501`. Kalau tidak, buka manual.

**Flow di UI:**

1. **Sidebar → pilih Chain** (default BSC)
2. **Sidebar → Candidates slider** (3-15, default 5)
3. **Sidebar → optional keyword filter**
4. **Click "Run Pipeline"** (tombol merah primary)
5. Lihat Phase 1 status box expand dengan "Calling smart_wallets..."
6. Phase 2 progress bar berjalan dari 1/N ke N/N
7. Hasil muncul dalam 4 metric cards (Verified / Approved / Review / Rejected)
8. Ranked wallet cards dengan badge warna verdict
9. **Click "Details" expander** pada wallet manapun untuk score breakdown
10. **Click "Mirror a trade"** pada APPROVED wallet untuk build quote command

**Demo-friendly tip:** Set Chain=BSC, Candidates=10, klik Run. Tunggu ~20 detik.
Biasanya akan ada 2-3 APPROVED, beberapa REVIEW, dan idealnya 1 REJECTED.

---

## 4. Demo Mode — Deterministic Output untuk Video Recording

Kalau mau rekam demo video dan API live tidak reliable (rate limit, network lag,
data berubah antar take), switch ke offline fixture mode:

### 4.1 CLI

```bash
# Bash / Git Bash / PowerShell
DEMO_MODE=1 python -m alphamirror.cli run --chain bsc --top 5

# Windows CMD
set DEMO_MODE=1
python -m alphamirror.cli run --chain bsc --top 5
```

### 4.2 Streamlit

```bash
# Bash
DEMO_MODE=1 python -m streamlit run app.py

# Windows CMD
set DEMO_MODE=1
python -m streamlit run app.py
```

### 4.3 Expected Output (Deterministic)

Dengan `DEMO_MODE=1` dan `run --top 5`, output selalu:

| Rank | Score | Verdict | Total P&L | Win Rate | Catatan |
|---:|---:|:---:|---:|---:|---|
| 1 | 97 | **APPROVED** | +$128,400 | 75% | Top tier |
| 2 | 97 | **APPROVED** | +$62,800 | 57% | Solid |
| 3 | 64 | REVIEW | +$144,306 | **13%** | 🎯 One-hit wonder (profit tinggi, win rate rendah) |
| 4 | 61 | REVIEW | +$18,200 | 52% | Moderate |
| 5 | 28 | **REJECTED** | **-$2,344** | 31% | 🎯 AVE flagged tapi loss |

**Narrative untuk video:**
- Focus ke rank #3 (one-hit wonder: "look at this — $144k profit but 13% win rate,
  clearly one lucky trade")
- Focus ke rank #5 (rejected: "AVE labeled this as smart money, but our verification
  shows a $2,344 loss — we reject it")

---

## 5. Example User Flows

### Flow A: "Find smart money on BSC, mirror a trade"

```bash
# 1. Discover + verify
python -m alphamirror.cli run --chain bsc --top 10

# 2. Pick the top APPROVED wallet from output (say 0x4b9c...)
# 3. Check its current holdings (the `run` output table shows Portfolio value)
# 4. Pick a token from that wallet (use Streamlit UI for easier drill-down)

# 5. Build mirror trade for $50 in a specific token
python -m alphamirror.cli mirror \
    --chain bsc \
    --token 0x_TOKEN_FROM_WALLET \
    --usd 50

# 6. Copy the docker command, run it in your own terminal, 
#    sign the returned tx in your wallet
```

### Flow B: "Watch approved wallets for new positions"

```bash
# 1. Run pipeline to find approved wallets
python -m alphamirror.cli run --chain bsc --top 10

# 2. Copy top 2-3 APPROVED addresses

# 3. Start watch loop (Ctrl+C to stop)
python -m alphamirror.cli watch \
    --wallet 0xAAA_APPROVED_1 \
    --wallet 0xBBB_APPROVED_2 \
    --chain bsc \
    --interval 60

# When a new position opens, you'll see:
#   OPEN wallet=0xAAA... token=ALPHA risk=SAFE
```

### Flow C: "Educational — see why a wallet is rejected"

```bash
# 1. Offline demo mode for deterministic output
DEMO_MODE=1 python -m alphamirror.cli run --chain bsc --top 5

# 2. Study the REJECTED row:
#    - It has $-2,344 total P&L
#    - 31% win rate
#    - AVE flagged it as smart money for 799 days
#    - Yet it's net unprofitable

# 3. Launch Streamlit UI (also in demo mode)
DEMO_MODE=1 python -m streamlit run app.py

# 4. Run pipeline → click Details on rejected wallet
#    → see full score breakdown and profit distribution bar chart
```

### Flow D: "Cross-chain check"

```bash
# Kata kunci: hackathon rubric menekankan multichain capability
python -m alphamirror.cli discover --chain bsc --top 3
python -m alphamirror.cli discover --chain eth --top 3
python -m alphamirror.cli discover --chain base --top 3
python -m alphamirror.cli discover --chain solana --top 3
```

---

## 6. Interpreting the Output

### 6.1 Verdict Meanings

| Verdict | Score | Action |
|---|:---:|---|
| **APPROVED** | ≥70 | Safe to mirror (di rubric kami). Consistent wins, not a one-hit wonder, active, reasonable portfolio. |
| **REVIEW** | 40–69 | Needs human judgment. Salah satu atau lebih signal-nya mediocre. |
| **REJECTED** | <40 | AVE flagged tapi numeriknya tidak mendukung. Skip. |

### 6.2 Score Breakdown Signals

Scoring 0-100, weighted average dari 6 signal:

| Weight | Signal | Good Example |
|---:|---|---|
| 25 | Profitability | Total profit >$50k → full 25 pts |
| 25 | Consistency | Win rate ≥55% + 3+ big wins + distributed (not one-hit) → full 25 pts |
| 15 | Recency | Last trade ≤3 hari → full 15 pts |
| 15 | Portfolio sanity | 3–30 positions, 10-80% blue chip → full 15 pts |
| 10 | Volume | ≥$1M lifetime volume → full 10 pts |
| 10 | Age | ≥180 days old → full 10 pts |

### 6.3 Red Flags

- **Win rate <40%** → consistency = 0 pts (scoring cap)
- **Concentration ratio ≥0.8** → hard ceiling at 69 (REVIEW max)
- **Last trade >30 days** → recency = 0 pts (dormant)
- **Age <30 days** → near-zero age score (anti-sybil)

---

## 7. Troubleshooting

### Error: `AVE_API_KEY not set`

**Solusi:**
1. Buat file `.env` di root project: `copy .env.example .env`
2. Edit `.env`, ganti `your_api_key_here` dengan key asli dari `cloud.ave.ai`
3. Pastikan file `.env` ada di **root** project (sama level dengan `README.md`)

### Error: `UnicodeEncodeError: 'charmap' codec`

**Solusi:** Sudah ter-fix di semua file project. Kalau masih muncul di script
custom, set environment variable:

```bash
# CMD
set PYTHONIOENCODING=utf-8

# PowerShell
$env:PYTHONIOENCODING = "utf-8"

# Bash
export PYTHONIOENCODING=utf-8
```

### Hasil `run` menunjukkan semua wallet REJECTED dengan $0

**Kemungkinan:** DEMO_MODE=1 dengan fixture lama atau cache. **Solusi:**

```bash
# Unset DEMO_MODE
set DEMO_MODE=
python -m alphamirror.cli run --chain bsc --top 5
```

### "Wallet not in AVE's smart wallet pool" di `verify`

**Normal.** AVE's smart_wallets pool hanya top 100 wallets dan berotasi.
Pakai `run` command yang auto-discover pool terbaru, atau coba lagi dengan
wallet yang baru saja muncul di `discover` output.

### Streamlit tidak bisa dibuka di browser

```bash
# Pastikan pakai python -m bukan streamlit langsung (streamlit binary tidak di PATH)
python -m streamlit run app.py

# Port kustom kalau 8501 sudah dipakai
python -m streamlit run app.py --server.port 8510
```

### Rate limit error (429) dari AVE

Kalau dapat `AVE API 429` error meski pakai rate limiter, kemungkinan sudah
hit daily quota free tier. Solusi: tunggu 1 jam atau gunakan `DEMO_MODE=1`
untuk offline testing.

---

## 8. Mapping: Form Submission ↔ Commands

Buat mas Huda yang sedang isi submission form AVE Claw:

| Form Field | Apa yang didemonstrasikan di video | Command |
|---|---|---|
| Monitoring Skill | Phase 4 watch loop detecting new positions | `python -m alphamirror.cli watch --wallet 0x... --chain bsc --interval 60` |
| Trading Skill | Phase 5 mirror quote command | `python -m alphamirror.cli mirror --chain bsc --token 0x... --usd 50` |
| Both (Complete App) | Full pipeline showing discovery + verification + mirror capability | `python -m alphamirror.cli run --chain bsc --top 10` + Streamlit UI |
| Web Application format | Streamlit interactive UI | `python -m streamlit run app.py` |

---

## 9. Commands untuk Demo Video (5-menit)

Urutan optimal untuk demo video recording:

```bash
# Setup (sebelum recording)
cd "F:\Hackathons\Hackathon Ave"
# Pastikan .env ada, API key valid
python scripts/smoke_test.py  # konfirmasi sehat

# OPSI A: Live data (lebih impressive tapi butuh network stable)
python -m streamlit run app.py
# → Di browser: pilih BSC, top=10, klik Run Pipeline, tunggu ~22 detik
# → Scroll hasil, drill down wallet REJECTED (kalau ada)
# → Click "Mirror a trade from this wallet" pada APPROVED wallet

# OPSI B: Offline deterministic (reliable tapi data tidak live)
DEMO_MODE=1 python -m streamlit run app.py
# → Sama seperti di atas, tapi fixed output: 2 APPROVED, 1 one-hit wonder REVIEW, 1 REJECTED

# Terminal window kedua (untuk narasi teknis di video):
python -m alphamirror.cli run --chain bsc --top 5
# → Tampilan rich table di terminal untuk closeup "11 endpoints, 2 skills"
```

Follow `DEMO_VIDEO_SCRIPT.md` untuk timeline per-30-detik dan voiceover.

---

## 10. Final Pre-Submit Checklist

Sebelum upload ke form hackathon:

```bash
# 1. Semua command jalan tanpa error
python scripts/smoke_test.py
python -m alphamirror.cli discover --chain bsc --top 3
python -m alphamirror.cli run --chain bsc --top 5
python -m alphamirror.cli mirror --chain bsc --token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c --usd 50

# 2. Offline mode jalan (safety net)
DEMO_MODE=1 python -m alphamirror.cli run --chain bsc --top 5

# 3. Streamlit boot
python -m streamlit run app.py
# browser test, lalu Ctrl+C

# 4. PDF dokumentasi ada dan valid
python -c "from pypdf import PdfReader; print('pages:', len(PdfReader('docs/AlphaMirror_Project_Documentation.pdf').pages))"

# 5. GitHub sync
git status  # harus "clean"
git log --oneline | head -5
```

**PDF untuk upload:** `F:\Hackathons\Hackathon Ave\docs\AlphaMirror_Project_Documentation.pdf`
**Repo URL:** `https://github.com/PugarHuda/AlphaMirror.git`

---

Kalau ada error atau pertanyaan, paste output lengkap-nya (command yang dipakai +
error message) dan saya bantu debug.
