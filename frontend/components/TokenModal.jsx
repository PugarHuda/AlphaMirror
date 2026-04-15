'use client';

import { useEffect, useState } from 'react';
import { apiFetch, shortAddr } from '@/lib/format';

export default function TokenModal({ chain, address, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    const realChain = ['bsc', 'eth', 'base', 'solana'].includes(chain) ? chain : 'bsc';
    apiFetch(`/api/token/${realChain}/${address}`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [chain, address]);

  const risk = data?.risk || {};
  const holders = data?.holders || [];
  const txs = data?.recent_txs || [];
  const kline = data?.kline || [];

  const isHoneypot = risk.is_honeypot === true || risk.is_honeypot === 'true' || risk.is_honeypot === 1;
  const buyTax = Number(risk.buy_tax || 0);
  const sellTax = Number(risk.sell_tax || 0);
  const riskLevel = isHoneypot ? 'DANGER' : (buyTax > 10 || sellTax > 10) ? 'HIGH' : 'SAFE';
  const riskClass = riskLevel === 'DANGER' ? 'verdict-REJECTED' : riskLevel === 'HIGH' ? 'verdict-REVIEW' : 'verdict-APPROVED';

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/70 backdrop-blur" onClick={onClose}>
      <div
        className="glass border border-outline-variant/20 rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto scroll-area"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-surface-container/90 backdrop-blur-xl border-b border-outline-variant/10 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <div className="text-xs text-on-surface-variant uppercase tracking-widest font-label">
              Token Analysis
            </div>
            <div className="font-mono text-sm mt-0.5 break-all">{address}</div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-surface-container-high rounded-lg">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && <div className="text-error text-sm">{error}</div>}

          {!data && !error && <div className="h-40 loading-shimmer rounded-xl" />}

          {data && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/10">
                  <div className="text-[10px] uppercase text-on-surface-variant font-label font-semibold mb-2">
                    Price Chart (48h)
                  </div>
                  <div className="h-24">
                    <KlineChart kline={kline} />
                  </div>
                  <div className="text-[10px] text-on-surface-variant font-mono mt-2">
                    via kline_token endpoint
                  </div>
                </div>
                <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/10">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-[10px] uppercase text-on-surface-variant font-label font-semibold">
                      Safety Check
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest ${riskClass}`}>
                      {riskLevel}
                    </span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <Row label="Honeypot" value={isHoneypot ? 'YES' : 'NO'} color={isHoneypot ? 'text-error' : 'text-success'} />
                    <Row label="Buy tax" value={`${buyTax}%`} mono />
                    <Row label="Sell tax" value={`${sellTax}%`} mono />
                  </div>
                  <div className="text-[10px] text-on-surface-variant font-mono mt-3">
                    via risk endpoint
                  </div>
                </div>
              </div>

              <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/10">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-bold text-sm">Top Holders</div>
                  <div className="text-[10px] text-on-surface-variant font-mono">
                    via holders endpoint · {holders.length} shown
                  </div>
                </div>
                <div className="space-y-1 max-h-40 overflow-y-auto scroll-area text-xs">
                  {holders.length === 0 ? (
                    <div className="text-on-surface-variant text-center py-4">no holders data</div>
                  ) : (
                    holders.slice(0, 10).map((h, i) => (
                      <div key={i} className="flex justify-between py-1 border-b border-outline-variant/5 last:border-0">
                        <span className="font-mono text-on-surface-variant">
                          {i + 1}. {shortAddr(h.address || h.holder_address || h.wallet_address || '')}
                        </span>
                        <span className="font-mono">{h.balance ? Number(h.balance).toFixed(2) : '-'}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/10">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-bold text-sm">Recent Swap Transactions</div>
                  <div className="text-[10px] text-on-surface-variant font-mono">
                    via txs endpoint · {txs.length} shown
                  </div>
                </div>
                <div className="text-xs text-on-surface-variant">
                  {txs.length === 0
                    ? 'No recent swaps returned.'
                    : `${txs.length} recent swap transactions streamed from the txs endpoint.`}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, color, mono }) {
  return (
    <div className="flex justify-between">
      <span className="text-on-surface-variant">{label}</span>
      <span className={`${color || ''} ${mono ? 'font-mono' : 'font-bold'}`}>{value}</span>
    </div>
  );
}

function KlineChart({ kline }) {
  if (!Array.isArray(kline) || kline.length < 2) {
    return (
      <div className="h-full flex items-center justify-center text-xs text-on-surface-variant">
        No kline data
      </div>
    );
  }
  const closes = kline
    .map((k) => (Array.isArray(k) ? Number(k[4]) : Number(k.close || 0)))
    .filter((n) => Number.isFinite(n));
  if (closes.length < 2) {
    return (
      <div className="h-full flex items-center justify-center text-xs text-on-surface-variant">
        No kline data
      </div>
    );
  }
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const w = 400;
  const h = 80;
  const step = w / (closes.length - 1);
  let d = '';
  closes.forEach((v, i) => {
    const x = i * step;
    const y = h - ((v - min) / range) * h;
    d += (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1) + ' ';
  });
  const area = d + `L${w},${h} L0,${h} Z`;
  const up = closes[closes.length - 1] >= closes[0];
  const color = up ? '#7dd08a' : '#ffb4ab';

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full">
      <defs>
        <linearGradient id="kGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#kGrad)" />
      <path d={d} fill="none" stroke={color} strokeWidth="2" />
    </svg>
  );
}
