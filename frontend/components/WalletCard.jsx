'use client';

import { fmtUSD, fmtPct } from '@/lib/format';

const DIST_LABELS = ['>10x', '5-10x', '3-5x', '2-4x', '1-2x', 'flat', '-10-50%', '-50-100%'];

export default function WalletCard({ wallet, rank, onDrillDown, onMirror }) {
  const c = wallet.candidate;
  const pd = wallet.profit_distribution;

  const lastTrade = c.days_since_last_trade != null ? `${c.days_since_last_trade}d ago` : 'unknown';
  const age = wallet.age_days != null ? `${wallet.age_days}d` : 'unknown';

  const dist = [pd.above_900, pd.p500_900, pd.p300_500, pd.p100_300, pd.p10_100, pd.flat, pd.small_loss, pd.big_loss];
  const maxDist = Math.max(1, ...dist);

  const scoreColor = wallet.score >= 70 ? 'text-success' : wallet.score >= 40 ? 'text-primary-container' : 'text-error';
  const canMirror = wallet.verdict === 'APPROVED' && wallet.holdings && wallet.holdings.length > 0;

  return (
    <div className="glass rounded-2xl border border-outline-variant/10 hover:border-primary-container/20 transition card-lift fade-in">
      <div className="p-5">
        <div className="flex items-start gap-4 mb-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center font-bold text-sm">
            {rank}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap mb-1">
              <span className="font-mono text-sm break-all">{wallet.address}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest verdict-${wallet.verdict}`}>
                {wallet.verdict}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-on-surface-variant flex-wrap">
              <span>Chain: <span className="text-on-surface uppercase font-semibold">{wallet.chain}</span></span>
              <span>Last trade: {lastTrade}</span>
              <span>Age: {age}</span>
            </div>
          </div>
          <div className="flex-shrink-0 text-right">
            <div className={`text-3xl font-extrabold ${scoreColor}`}>{wallet.score}</div>
            <div className="text-[10px] text-on-surface-variant font-label uppercase tracking-widest">Score</div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          <MetricBox label="Total P&L" value={fmtUSD(c.total_profit_usd, true)} accent={c.total_profit_usd >= 0 ? 'success' : 'error'} />
          <MetricBox label="Win Rate" value={fmtPct(c.token_profit_rate)} />
          <MetricBox label="Trades" value={c.total_trades} />
          <MetricBox label="Big Wins 2x+" value={pd.big_wins} />
          <MetricBox label="Portfolio" value={fmtUSD(wallet.portfolio_value_usd)} />
        </div>

        <details className="group">
          <summary className="cursor-pointer text-xs text-primary-container font-bold uppercase tracking-widest font-label flex items-center gap-2 select-none">
            <span className="material-symbols-outlined text-sm group-open:rotate-180 transition">expand_more</span>
            Details
          </summary>
          <div className="pt-5 grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <div className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label mb-3">
                Score Breakdown
              </div>
              <ul className="space-y-1">
                {wallet.reasons.map((r, i) => (
                  <li key={i} className="text-xs text-on-surface-variant py-1 border-b border-outline-variant/5 last:border-0">
                    {r}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label mb-3">
                Profit Tier Distribution
              </div>
              <div className="flex items-end gap-1 bg-surface-container-low rounded-lg p-3">
                {dist.map((v, i) => {
                  const h = (v / maxDist) * 100;
                  const color = i <= 3 ? 'bg-success/70' : i === 4 ? 'bg-primary-container/70' : 'bg-error/70';
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div className="w-full flex items-end justify-center" style={{ height: 40 }}>
                        <div className={`w-5 ${color} rounded-t`} style={{ height: `${h}%` }} title={`${DIST_LABELS[i]}: ${v}`} />
                      </div>
                      <div className="text-[9px] text-on-surface-variant font-label mt-1">{DIST_LABELS[i]}</div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-3 text-[11px] text-on-surface-variant">
                Concentration: <span className="text-on-surface font-mono">{(pd.concentration_ratio * 100).toFixed(0)}%</span>
                {pd.concentration_ratio >= 0.8 && (
                  <span className="text-error ml-2">(one-hit wonder cap applied)</span>
                )}
              </div>
            </div>
          </div>

          <div className="pt-5 flex gap-2 flex-wrap">
            <button
              onClick={onDrillDown}
              className="px-4 py-2 bg-surface-container-high hover:bg-surface-container-highest rounded-lg text-xs font-bold flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-base">account_circle</span>
              Deep wallet scan
            </button>
            {canMirror && (
              <button
                onClick={onMirror}
                className="px-4 py-2 bg-primary-container/20 hover:bg-primary-container/30 text-primary-container border border-primary-container/30 rounded-lg text-xs font-bold flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-base">swap_horiz</span>
                Build mirror trade
              </button>
            )}
          </div>
        </details>
      </div>
    </div>
  );
}

function MetricBox({ label, value, accent }) {
  const textClass = accent === 'success' ? 'text-success' : accent === 'error' ? 'text-error' : '';
  return (
    <div className="bg-surface-container-low rounded-lg p-3">
      <div className="text-[10px] text-on-surface-variant font-label font-semibold uppercase">{label}</div>
      <div className={`text-base font-bold ${textClass}`}>{value}</div>
    </div>
  );
}
