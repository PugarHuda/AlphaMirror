"""
Verification Score formula for AlphaMirror.

Unlike Phase 1 where we trust AVE's smart_wallets classifier blindly, this
scoring function stress-tests each wallet against 5 independent quality
dimensions. The premise: "AVE says this wallet made $148k profit — but is
that profit the kind we'd actually want to mirror?"

Scoring is 0–100. Thresholds:
  APPROVED  : >= 70  (mirror-worthy)
  REVIEW    : 40-69  (user judges)
  REJECTED  : < 40   (AVE flagged but quality check failed)
"""

from __future__ import annotations

from .models import VerifiedWallet


# Weights sum to 100
W_PROFITABILITY = 25    # Is total_profit meaningfully positive?
W_CONSISTENCY = 25      # Wins spread across trades, not one-hit wonder?
W_RECENCY = 15          # Actively trading (not dormant smart money)?
W_PORTFOLIO = 15        # Has real positions, rational mix?
W_VOLUME = 10           # Enough volume to be a serious wallet?
W_AGE = 10              # Old enough to survive anti-sybil filter?

APPROVED_THRESHOLD = 70
REVIEW_THRESHOLD = 40


def score_wallet(v: VerifiedWallet) -> VerifiedWallet:
    """Mutates v with score, verdict, and human-readable reasons."""
    c = v.candidate
    pd = c.profit_distribution

    reasons: list[str] = []
    total = 0.0

    # --- 1. Profitability (25 pts) ---
    profit = c.total_profit_usd
    if profit >= 50_000:
        pts = W_PROFITABILITY
        reasons.append(f"profitability: +{pts:.0f} — +${profit:,.0f} realized")
    elif profit >= 10_000:
        pts = W_PROFITABILITY * 0.75
        reasons.append(f"profitability: +{pts:.0f} — +${profit:,.0f} realized")
    elif profit > 0:
        pts = W_PROFITABILITY * 0.4
        reasons.append(f"profitability: +{pts:.0f} — +${profit:,.0f} (marginal)")
    else:
        pts = 0
        reasons.append(f"profitability: +0 — ${profit:,.0f} (unprofitable)")
    total += pts

    # --- 2. Consistency (25 pts) — the one-hit-wonder detector ---
    # We reward wallets whose wins are spread across tiers, not concentrated
    # in one lucky 10x trade.
    win_rate = c.token_profit_rate
    big_win_count = pd.big_wins
    conc = pd.concentration_ratio

    if win_rate >= 0.55 and big_win_count >= 3 and conc < 0.7:
        pts = W_CONSISTENCY
        reasons.append(
            f"consistency: +{pts:.0f} — {win_rate:.0%} win rate, "
            f"{big_win_count} big wins well-distributed"
        )
    elif win_rate >= 0.5 and big_win_count >= 2:
        pts = W_CONSISTENCY * 0.7
        reasons.append(
            f"consistency: +{pts:.0f} — {win_rate:.0%} win rate, "
            f"{big_win_count} big win(s)"
        )
    elif win_rate >= 0.4:
        pts = W_CONSISTENCY * 0.4
        reasons.append(f"consistency: +{pts:.0f} — {win_rate:.0%} win rate (mediocre)")
    else:
        pts = 0
        reasons.append(f"consistency: +0 — {win_rate:.0%} win rate (mostly losing)")

    # Penalty for one-hit-wonder pattern
    if big_win_count >= 1 and conc >= 0.8:
        pts = max(0, pts - 8)
        reasons.append(f"  ↳ one-hit-wonder penalty: {conc:.0%} of big wins from one bucket")
    total += pts

    # --- 3. Recency (15 pts) ---
    days = c.days_since_last_trade
    if days is None:
        pts = W_RECENCY * 0.5
        reasons.append(f"recency: +{pts:.0f} — last trade time unknown")
    elif days <= 3:
        pts = W_RECENCY
        reasons.append(f"recency: +{pts:.0f} — active ({days}d since last trade)")
    elif days <= 14:
        pts = W_RECENCY * 0.7
        reasons.append(f"recency: +{pts:.0f} — active ({days}d)")
    elif days <= 30:
        pts = W_RECENCY * 0.4
        reasons.append(f"recency: +{pts:.0f} — slowing ({days}d since last trade)")
    else:
        pts = 0
        reasons.append(f"recency: +0 — dormant ({days}d since last trade)")
    total += pts

    # --- 4. Portfolio sanity (15 pts) ---
    n = v.portfolio_size
    bc = v.blue_chip_ratio
    if n == 0:
        pts = 0
        reasons.append("portfolio: +0 — empty (may have fully rotated out)")
    elif 3 <= n <= 30 and 0.1 <= bc <= 0.8:
        pts = W_PORTFOLIO
        reasons.append(
            f"portfolio: +{pts:.0f} — {n} positions, {bc:.0%} blue chip (balanced)"
        )
    elif n >= 2:
        pts = W_PORTFOLIO * 0.5
        reasons.append(
            f"portfolio: +{pts:.0f} — {n} positions, {bc:.0%} blue chip (imbalanced)"
        )
    else:
        pts = W_PORTFOLIO * 0.2
        reasons.append(f"portfolio: +{pts:.0f} — thin ({n} position)")
    total += pts

    # --- 5. Volume (10 pts) — is this a serious wallet or test account? ---
    vol = c.total_volume_usd
    if vol >= 1_000_000:
        pts = W_VOLUME
        reasons.append(f"volume: +{pts:.0f} — ${vol:,.0f} lifetime volume")
    elif vol >= 100_000:
        pts = W_VOLUME * 0.7
        reasons.append(f"volume: +{pts:.0f} — ${vol:,.0f} lifetime volume")
    elif vol >= 10_000:
        pts = W_VOLUME * 0.4
        reasons.append(f"volume: +{pts:.0f} — ${vol:,.0f} (small trader)")
    else:
        pts = 0
        reasons.append(f"volume: +0 — ${vol:,.0f} (too thin)")
    total += pts

    # --- 6. Age (10 pts) — anti-sybil ---
    age = v.age_days
    if age is None:
        pts = W_AGE * 0.5
        reasons.append(f"age: +{pts:.0f} — age unknown")
    elif age >= 180:
        pts = W_AGE
        reasons.append(f"age: +{pts:.0f} — {age}d (established)")
    elif age >= 30:
        pts = W_AGE * 0.6
        reasons.append(f"age: +{pts:.0f} — {age}d (moderate)")
    else:
        pts = W_AGE * 0.1
        reasons.append(f"age: +{pts:.0f} — {age}d (fresh, suspicious)")
    total += pts

    v.score = round(total, 1)
    v.reasons = reasons

    if v.score >= APPROVED_THRESHOLD:
        v.verdict = "APPROVED"
    elif v.score >= REVIEW_THRESHOLD:
        v.verdict = "REVIEW"
    else:
        v.verdict = "REJECTED"

    return v
