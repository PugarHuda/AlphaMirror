"""
AlphaMirror — Streamlit UI

Run:
    streamlit run app.py

The UI exposes the same pipeline as the CLI but with visual polish for the
demo video. Key demo moments it's designed to produce:

  1. Watching the "Verifying..." progress bar tick through candidates live
  2. The APPROVED / REVIEW / REJECTED badges appearing with score breakdowns
  3. Expandable wallet cards showing profit-tier distribution charts
  4. The mirror trade preview showing a self-custody command (no keys needed)
"""

from __future__ import annotations

import streamlit as st

from alphamirror.client_factory import make_client
from alphamirror.discovery import discover_candidates
from alphamirror.verification import verify_all, verify_one
from alphamirror.mirror import build_mirror_preview
from alphamirror.models import VerifiedWallet


# ---------- page config ----------

st.set_page_config(
    page_title="AlphaMirror — Verified Smart Money",
    page_icon="AM",
    layout="wide",
)

VERDICT_COLORS = {
    "APPROVED": "#16a34a",
    "REVIEW": "#ca8a04",
    "REJECTED": "#dc2626",
}

CHAINS = ["bsc", "eth", "base", "solana"]


# ---------- header ----------

st.title("AlphaMirror")
st.caption(
    "Verified smart-money copy-trading. AVE Cloud says this wallet made $148k "
    "profit — we stress-test whether that profit is the kind you'd actually "
    "want to mirror."
)
st.markdown(
    "Built on [AVE Cloud Skill](https://github.com/AveCloud/ave-cloud-skill) · "
    "Non-custodial · Self-custody execution via `trade-chain-wallet`"
)
st.divider()


# ---------- sidebar controls ----------

with st.sidebar:
    st.header("Pipeline Controls")
    chain = st.selectbox("Chain", CHAINS, index=0)
    top_n = st.slider("Candidates to verify", min_value=3, max_value=15, value=5)
    keyword = st.text_input("Token/keyword filter (optional)", value="")
    run_button = st.button("Run Pipeline", type="primary", use_container_width=True)
    st.divider()
    st.subheader("Notes")
    st.markdown(
        "- Free tier = **1 TPS** — verifying 5 wallets takes ~10s\n"
        "- We call `smart_wallets`, `wallet_info`, `wallet_tokens`\n"
        "- No private keys required — mirror trades are self-custody"
    )
    st.divider()
    st.caption("Set `DEMO_MODE=1` to use offline fixture data for a reliable demo.")


# ---------- session state ----------

if "verified" not in st.session_state:
    st.session_state.verified = []
if "ran_once" not in st.session_state:
    st.session_state.ran_once = False


# ---------- run pipeline ----------


def run_pipeline(chain: str, top_n: int, keyword: str) -> list[VerifiedWallet]:
    with make_client() as ave:
        with st.status("Phase 1: Discovering smart money candidates...", expanded=True) as status:
            st.write("Calling `smart_wallets`...")
            candidates = discover_candidates(
                ave,
                chain=chain,
                keyword=keyword or None,
                max_candidates=top_n,
            )
            status.update(
                label=f"Phase 1: {len(candidates)} candidates retrieved",
                state="complete",
            )

        if not candidates:
            st.error("No smart wallets returned for this chain/keyword.")
            return []

        progress = st.progress(0.0, text="Phase 2: Starting verification...")
        results: list[VerifiedWallet] = []
        for i, c in enumerate(candidates, start=1):
            progress.progress(
                (i - 1) / len(candidates),
                text=f"Phase 2: Verifying {i}/{len(candidates)} — {c.address[:10]}...",
            )
            v = verify_one(ave, c)
            results.append(v)
        progress.progress(1.0, text=f"Phase 2: Done ({len(results)} wallets scored)")

        results.sort(key=lambda w: w.score, reverse=True)
        return results


if run_button:
    st.session_state.verified = run_pipeline(chain, top_n, keyword)
    st.session_state.ran_once = True


# ---------- results ----------


def render_verdict_badge(verdict: str) -> str:
    color = VERDICT_COLORS.get(verdict, "#6b7280")
    return (
        f'<span style="background:{color};color:white;padding:4px 10px;'
        f'border-radius:6px;font-weight:600;font-size:0.85rem">{verdict}</span>'
    )


def render_summary(verified: list[VerifiedWallet]) -> None:
    approved = [v for v in verified if v.verdict == "APPROVED"]
    review = [v for v in verified if v.verdict == "REVIEW"]
    rejected = [v for v in verified if v.verdict == "REJECTED"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verified", len(verified))
    c2.metric("Approved", len(approved), delta=None)
    c3.metric("Review", len(review), delta=None)
    c4.metric("Rejected", len(rejected), delta=None)

    if rejected:
        st.warning(
            f"**{len(rejected)} wallet(s) REJECTED** — AVE flagged these as "
            "smart money but our verification shows they don't meet our quality "
            "bar. This is the core AlphaMirror value: not every 'smart wallet' "
            "is actually worth mirroring."
        )


def render_wallet_card(v: VerifiedWallet, rank: int) -> None:
    c = v.candidate
    pd = c.profit_distribution

    with st.container(border=True):
        top = st.columns([3, 2, 2, 2])
        top[0].markdown(
            f"**#{rank}** `{v.address}`",
            help="Click ' Details' below for full score breakdown",
        )
        top[1].markdown(render_verdict_badge(v.verdict), unsafe_allow_html=True)
        top[2].metric("Score", f"{v.score:.0f}/100", label_visibility="visible")
        profit_color = "normal" if c.total_profit_usd >= 0 else "inverse"
        top[3].metric(
            "Total P&L",
            f"${c.total_profit_usd:,.0f}",
            delta=f"{c.total_profit_rate * 100:.1f}% ROI",
            delta_color=profit_color,
        )

        m = st.columns(6)
        m[0].metric("Win Rate", f"{c.token_profit_rate * 100:.0f}%")
        m[1].metric("Trades", f"{c.total_trades:,}")
        m[2].metric("Big Wins (2x+)", pd.big_wins)
        m[3].metric("Volume", f"${c.total_volume_usd:,.0f}")
        m[4].metric("Age", f"{v.age_days}d" if v.age_days else "-")
        m[5].metric("Portfolio", f"${v.portfolio_value_usd:,.0f}")

        with st.expander("Details"):
            d1, d2 = st.columns(2)

            with d1:
                st.markdown("**Score breakdown**")
                for reason in v.reasons:
                    st.markdown(f"- {reason}")

            with d2:
                st.markdown("**Profit distribution (per trade)**")
                dist_data = {
                    "Tier": [
                        ">10x", "5-10x", "3-5x", "2-4x",
                        "1.1-2x", "Flat", "-10 to -50%", "-50 to -100%",
                    ],
                    "Count": [
                        pd.above_900, pd.p500_900, pd.p300_500, pd.p100_300,
                        pd.p10_100, pd.flat, pd.small_loss, pd.big_loss,
                    ],
                }
                st.bar_chart(dist_data, x="Tier", y="Count", height=250)
                if c.last_trade_time:
                    days = c.days_since_last_trade
                    st.caption(f"Last trade: {days}d ago")
                if c.top_tokens:
                    st.markdown("**Top traded tokens**")
                    for t in c.top_tokens[:5]:
                        vol = t.get("volume", 0)
                        sym = t.get("symbol", "?")
                        st.caption(f"- {sym}: ${vol:,.0f} volume")

        if v.verdict == "APPROVED" and v.holdings:
            with st.expander("Mirror a trade from this wallet"):
                current = [h for h in v.holdings if h.token_address and not h.is_blue_chip]
                if current:
                    choice = st.selectbox(
                        "Pick a token currently held by this wallet to mirror",
                        options=[h.token_address for h in current],
                        format_func=lambda a: next(
                            (f"{h.symbol} (${h.balance_usd:,.0f})"
                             for h in current if h.token_address == a),
                            a,
                        ),
                        key=f"mirror_{v.address}",
                    )
                    usd = st.number_input(
                        "Mirror size (USD)",
                        min_value=10.0,
                        max_value=500.0,
                        value=50.0,
                        step=10.0,
                        key=f"usd_{v.address}",
                    )
                    if st.button("Build self-custody quote", key=f"btn_{v.address}"):
                        preview = build_mirror_preview(
                            chain=v.chain,
                            out_token=choice,
                            in_amount_usd=float(usd),
                        )
                        st.success("Quote command ready — sign it in your wallet:")
                        st.code(preview.command, language="bash")
                        st.caption(
                            "This command returns an unsigned transaction "
                            "payload. You sign it in your own wallet app. "
                            "AlphaMirror never touches your keys."
                        )
                else:
                    st.caption("No non-bluechip positions currently held.")


# ---------- main render ----------

if st.session_state.ran_once:
    verified = st.session_state.verified
    if verified:
        st.subheader("Results")
        render_summary(verified)
        st.markdown("### Ranked Wallets")
        for i, v in enumerate(verified, start=1):
            render_wallet_card(v, i)
else:
    st.info(
        "**Welcome.** Click **Run Pipeline** in the sidebar to discover and "
        "verify smart money wallets on the selected chain. The full flow uses "
        "3 AVE skills (discover, verify, mirror-ready) and stays entirely on "
        "the free API tier."
    )
    st.markdown(
        "### How AlphaMirror differs\n"
        "- **Most copy-trading tools** rank wallets by raw P&L — which means "
        "one lucky 100x trade dominates and misleads you.\n"
        "- **AlphaMirror** cross-checks AVE's classification against 6 "
        "independent signals: profitability, trade-tier distribution, "
        "recency, portfolio sanity, volume, and wallet age.\n"
        "- **The killer output:** wallets AVE flagged that we **reject** — "
        "proving that 'smart money' labels aren't enough."
    )
