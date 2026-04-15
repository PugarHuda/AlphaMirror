'use client';

import { useEffect, useState } from 'react';
import { apiFetch, fmtUSD, shortAddr } from '@/lib/format';

export default function WalletModal({ chain, address, onClose, onTokenClick }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    apiFetch(`/api/wallet/${chain}/${address}`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [chain, address]);

  const info = data?.wallet_info || {};
  const holdings = data?.holdings || [];
  const activity = data?.activity || [];

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur" onClick={onClose}>
      <div
        className="glass border border-outline-variant/20 rounded-3xl max-w-5xl w-full max-h-[90vh] overflow-y-auto scroll-area"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-surface-container/90 backdrop-blur-xl border-b border-outline-variant/10 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <div className="text-xs text-on-surface-variant uppercase tracking-widest font-label">
              Wallet Drill-down
            </div>
            <div className="font-mono text-sm mt-0.5 break-all">{address}</div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-surface-container-high rounded-lg">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && <div className="text-error text-sm">{error}</div>}

          {!data && !error && (
            <>
              <div className="h-20 loading-shimmer rounded-xl" />
              <div className="h-40 loading-shimmer rounded-xl" />
              <div className="h-24 loading-shimmer rounded-xl" />
            </>
          )}

          {data && (
            <>
              {/* Aggregate metrics (from wallet_info) */}
              <div className="grid grid-cols-3 gap-3">
                <InfoCard
                  label="Total Balance"
                  value={info.total_balance ? `$${Number(info.total_balance).toFixed(0)}` : '-'}
                />
                <InfoCard
                  label="Win Ratio"
                  value={info.total_win_ratio ? `${Number(info.total_win_ratio).toFixed(0)}%` : '-'}
                />
                <InfoCard
                  label="Total Profit"
                  value={info.total_profit ? fmtUSD(Number(info.total_profit), true) : '-'}
                />
              </div>

              {/* Holdings with per-token P&L (address_pnl) */}
              <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
                <div className="px-4 py-3 border-b border-outline-variant/10 flex items-center justify-between">
                  <div className="font-bold text-sm">Top Holdings with Per-Token P&amp;L</div>
                  <div className="text-[10px] text-on-surface-variant font-mono">via address_pnl endpoint</div>
                </div>
                <div className="overflow-x-auto scroll-area">
                  <table className="w-full text-sm">
                    <thead className="bg-surface-container">
                      <tr className="text-[10px] uppercase text-on-surface-variant font-label font-semibold">
                        <th className="text-left py-2 px-3">Token</th>
                        <th className="text-right py-2 px-3">Value</th>
                        <th className="text-right py-2 px-3">Realized</th>
                        <th className="text-right py-2 px-3">Unrealized</th>
                        <th className="text-right py-2 px-3">Total P&amp;L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {holdings.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="py-6 text-center text-on-surface-variant text-xs">
                            no holdings returned
                          </td>
                        </tr>
                      ) : (
                        holdings.map((h, idx) => {
                          const pnl = h._pnl || {};
                          const realized = Number(pnl.realized_pnl || pnl.realized_profit || 0);
                          const unrealized = Number(pnl.unrealized_pnl || pnl.unrealized_profit || 0);
                          const total = realized + unrealized;
                          const tokenAddr = h.token_address || h.token || h.address || '';
                          return (
                            <tr key={idx} className="border-b border-outline-variant/5 hover:bg-surface-container-high/50">
                              <td className="py-3 px-3">
                                <button
                                  onClick={() => onTokenClick(chain, tokenAddr)}
                                  className="text-left"
                                >
                                  <div className="font-bold text-sm hover:text-primary-container transition">
                                    {h.symbol || '?'}
                                  </div>
                                  <div className="font-mono text-[10px] text-on-surface-variant">
                                    {shortAddr(tokenAddr)}
                                  </div>
                                </button>
                              </td>
                              <td className="py-3 px-3 text-right font-mono text-sm">
                                {fmtUSD(h.value_usd || h.balance_usd || 0)}
                              </td>
                              <td className={`py-3 px-3 text-right font-mono text-sm ${realized >= 0 ? 'text-success' : 'text-error'}`}>
                                {fmtUSD(realized, true)}
                              </td>
                              <td className={`py-3 px-3 text-right font-mono text-sm ${unrealized >= 0 ? 'text-success' : 'text-error'}`}>
                                {fmtUSD(unrealized, true)}
                              </td>
                              <td className={`py-3 px-3 text-right font-mono text-sm font-bold ${total >= 0 ? 'text-success' : 'text-error'}`}>
                                {fmtUSD(total, true)}
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Activity (address_txs) */}
              <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
                <div className="px-4 py-3 border-b border-outline-variant/10 flex items-center justify-between">
                  <div className="font-bold text-sm">Recent Activity</div>
                  <div className="text-[10px] text-on-surface-variant font-mono">
                    via address_txs endpoint · {activity.length} entries
                  </div>
                </div>
                <div className="p-4 text-xs text-on-surface-variant">
                  {activity.length === 0
                    ? 'No recent activity returned.'
                    : `Wallet has ${activity.length} recent on-chain events streamed from the address_txs endpoint.`}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoCard({ label, value }) {
  return (
    <div className="bg-surface-container-low rounded-lg p-3 border border-outline-variant/10">
      <div className="text-[10px] uppercase text-on-surface-variant font-label font-semibold">{label}</div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  );
}
