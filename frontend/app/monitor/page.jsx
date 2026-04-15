'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import Nav from '@/components/Nav';
import { apiFetch, shortAddr, fmtUSD } from '@/lib/format';

const POLL_INTERVAL_MS = 30_000; // 30s between snapshots
const STORAGE_KEY = 'alphamirror.watchlist';

export default function MonitorPage() {
  const [chain, setChain] = useState('bsc');
  const [watchlist, setWatchlist] = useState([]); // array of addresses
  const [addInput, setAddInput] = useState('');
  const [snapshots, setSnapshots] = useState({}); // addr -> [holdings]
  const [signals, setSignals] = useState([]); // detected events
  const [trending, setTrending] = useState([]);
  const [polling, setPolling] = useState(false);
  const [lastPoll, setLastPoll] = useState(null);
  const [error, setError] = useState(null);

  const snapshotsRef = useRef(snapshots);
  snapshotsRef.current = snapshots;

  // Load watchlist from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setWatchlist(JSON.parse(saved));
    } catch (e) {}
  }, []);

  // Save watchlist
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
    } catch (e) {}
  }, [watchlist]);

  // Load trending on mount + chain change
  useEffect(() => {
    apiFetch(`/api/trending/${chain}?page_size=8`)
      .then((d) => setTrending(d.items || []))
      .catch(() => setTrending([]));
  }, [chain]);

  const addWatch = () => {
    const addr = addInput.trim().toLowerCase();
    if (!addr || !addr.startsWith('0x') || addr.length < 10) {
      setError('Invalid address');
      return;
    }
    if (watchlist.includes(addr)) {
      setError('Already watching');
      return;
    }
    if (watchlist.length >= 5) {
      setError('Max 5 wallets (free tier rate limit budget)');
      return;
    }
    setError(null);
    setWatchlist([...watchlist, addr]);
    setAddInput('');
  };

  const removeWatch = (addr) => {
    setWatchlist(watchlist.filter((a) => a !== addr));
    setSnapshots((prev) => {
      const next = { ...prev };
      delete next[addr];
      return next;
    });
  };

  const pollOnce = useCallback(async () => {
    if (watchlist.length === 0) return;
    setPolling(true);
    setError(null);
    try {
      const q = new URLSearchParams({ wallets: watchlist.join(','), chain });
      const data = await apiFetch(`/api/monitor/snapshot?${q.toString()}`);

      const newSignals = [];
      const prevSnaps = snapshotsRef.current;

      for (const addr of watchlist) {
        const currentHoldings = data.snapshots[addr] || [];
        const prev = prevSnaps[addr];
        if (prev && Array.isArray(prev)) {
          const prevTokens = new Set(prev.map((h) => (h.token_address || h.token || '').toLowerCase()));
          const currTokens = new Set(currentHoldings.map((h) => (h.token_address || h.token || '').toLowerCase()));

          // New positions
          for (const h of currentHoldings) {
            const tAddr = (h.token_address || h.token || '').toLowerCase();
            if (tAddr && !prevTokens.has(tAddr)) {
              // Run risk check via dedicated endpoint
              let risk = null;
              try {
                const r = await apiFetch(`/api/monitor/risk/${chain}/${tAddr}`);
                risk = r.risk;
              } catch (e) {
                risk = null;
              }
              const riskVerdict = computeRiskVerdict(risk);
              newSignals.push({
                at: Date.now(),
                wallet: addr,
                action: 'OPEN',
                token: h.symbol || '?',
                token_address: tAddr,
                value_usd: Number(h.value_usd || h.balance_usd || 0),
                risk: riskVerdict,
              });
            }
          }
          // Exits
          for (const h of prev) {
            const tAddr = (h.token_address || h.token || '').toLowerCase();
            if (tAddr && !currTokens.has(tAddr)) {
              newSignals.push({
                at: Date.now(),
                wallet: addr,
                action: 'EXIT',
                token: h.symbol || '?',
                token_address: tAddr,
                value_usd: Number(h.value_usd || h.balance_usd || 0),
                risk: null,
              });
            }
          }
        }
      }

      setSnapshots(data.snapshots);
      if (newSignals.length > 0) {
        setSignals((prev) => [...newSignals, ...prev].slice(0, 50));
      }
      setLastPoll(Date.now());
    } catch (err) {
      setError(err.message);
    } finally {
      setPolling(false);
    }
  }, [chain, watchlist]);

  // Auto-poll every 30s when there are watched wallets
  useEffect(() => {
    if (watchlist.length === 0) return;
    pollOnce();
    const timer = setInterval(pollOnce, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [watchlist, chain, pollOnce]);

  return (
    <>
      <Nav />
      <main className="max-w-[1600px] mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6 min-h-[calc(100vh-4rem)]">

        {/* Sidebar */}
        <aside className="h-fit space-y-5 lg:sticky lg:top-24">
          <div className="glass rounded-2xl p-6 border border-outline-variant/10">
            <h3 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label mb-5">
              Watch Configuration
            </h3>

            <label className="block mb-4">
              <div className="text-xs text-on-surface-variant mb-2 font-label font-semibold">Chain</div>
              <select
                value={chain}
                onChange={(e) => setChain(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2.5 text-sm font-medium focus:border-primary-container focus:outline-none"
              >
                <option value="bsc">BSC</option>
                <option value="eth">Ethereum</option>
                <option value="base">Base</option>
                <option value="solana">Solana</option>
              </select>
            </label>

            <label className="block mb-4">
              <div className="text-xs text-on-surface-variant mb-2 font-label font-semibold">
                Add wallet to watch
              </div>
              <input
                type="text"
                value={addInput}
                onChange={(e) => setAddInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addWatch()}
                placeholder="0x..."
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2.5 text-sm font-mono focus:border-primary-container focus:outline-none"
              />
            </label>

            <button
              onClick={addWatch}
              className="w-full py-2.5 bg-primary-container text-on-primary rounded-lg font-bold text-sm hover:brightness-110 transition flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-base">add</span>
              Add to watchlist
            </button>

            {error && <div className="mt-3 text-xs text-error">{error}</div>}

            <div className="mt-5 pt-5 border-t border-outline-variant/10 text-xs text-on-surface-variant leading-relaxed">
              <div className="flex items-start gap-2">
                <span className="material-symbols-outlined text-sm mt-0.5">info</span>
                <span>Max 5 wallets on free tier. Polls every 30s. Risk check runs on every new position.</span>
              </div>
            </div>
          </div>

          <div className="glass rounded-2xl p-6 border border-outline-variant/10">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label">
                Poll Status
              </h3>
              <span className={`w-2 h-2 rounded-full ${polling ? 'bg-primary-container animate-pulse' : watchlist.length > 0 ? 'bg-success' : 'bg-on-surface-variant'}`} />
            </div>
            <div className="text-xs text-on-surface-variant space-y-1">
              <div>Watching: <span className="text-on-surface font-bold">{watchlist.length}/5</span></div>
              <div>Last poll: <span className="text-on-surface">{lastPoll ? `${Math.round((Date.now() - lastPoll) / 1000)}s ago` : 'never'}</span></div>
              <div>Signals: <span className="text-on-surface font-bold">{signals.length}</span></div>
            </div>
          </div>
        </aside>

        {/* Main */}
        <section className="space-y-6">
          <div className="glass rounded-2xl p-6 border border-outline-variant/10 relative overflow-hidden">
            <div className="absolute inset-0 grid-bg pointer-events-none opacity-60" />
            <div className="relative">
              <h1 className="text-2xl font-extrabold mb-1">Live Monitor</h1>
              <p className="text-on-surface-variant text-sm">
                Phase 4: poll approved wallets for new positions. Every new token triggers an automatic risk check via AVE&apos;s <code className="text-primary-container">risk</code> endpoint.
              </p>
            </div>
          </div>

          {/* Watchlist snapshots */}
          <div>
            <h2 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label mb-3">
              Watched Wallets · Current Holdings
            </h2>
            {watchlist.length === 0 ? (
              <div className="glass rounded-2xl p-12 border border-outline-variant/10 text-center">
                <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-4">radar</span>
                <h3 className="text-xl font-bold mb-2">No wallets watched yet</h3>
                <p className="text-on-surface-variant text-sm max-w-md mx-auto">
                  Add an address in the sidebar to start monitoring. Use approved wallets from the{' '}
                  <a href="/dashboard" className="text-primary-container hover:underline">dashboard</a>.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {watchlist.map((addr) => {
                  const holdings = snapshots[addr] || [];
                  return (
                    <div key={addr} className="glass rounded-2xl p-5 border border-outline-variant/10">
                      <div className="flex items-center justify-between mb-3">
                        <div className="font-mono text-sm break-all">{addr}</div>
                        <button
                          onClick={() => removeWatch(addr)}
                          className="p-1.5 hover:bg-error/10 hover:text-error rounded-lg transition"
                        >
                          <span className="material-symbols-outlined text-base">close</span>
                        </button>
                      </div>
                      <div className="text-[10px] uppercase text-on-surface-variant font-label font-semibold mb-2">
                        Current Holdings ({holdings.length}) · via wallet_tokens endpoint
                      </div>
                      {holdings.length === 0 ? (
                        <div className="text-xs text-on-surface-variant">
                          {polling ? 'Loading...' : 'No holdings or still loading'}
                        </div>
                      ) : (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          {holdings.slice(0, 8).map((h, i) => (
                            <div key={i} className="bg-surface-container-low rounded-lg px-3 py-2 text-xs">
                              <div className="font-bold text-on-surface truncate">{h.symbol || '?'}</div>
                              <div className="text-on-surface-variant font-mono">
                                {fmtUSD(h.value_usd || h.balance_usd || 0)}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Signal feed */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label">
                Signal Feed
              </h2>
              <div className="text-[10px] text-on-surface-variant font-mono">
                risk-gated via risk endpoint
              </div>
            </div>
            {signals.length === 0 ? (
              <div className="glass rounded-2xl p-8 border border-outline-variant/10 text-center text-on-surface-variant text-sm">
                No signals detected yet. Events appear here when a watched wallet opens or exits a position.
              </div>
            ) : (
              <div className="space-y-2">
                {signals.map((s, i) => (
                  <SignalRow key={i} signal={s} />
                ))}
              </div>
            )}
          </div>

          {/* Trending discovery */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label">
                Trending Now on {chain.toUpperCase()}
              </h2>
              <div className="text-[10px] text-on-surface-variant font-mono">
                via trending endpoint
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {trending.length === 0 ? (
                <div className="col-span-full glass rounded-xl p-6 text-center text-xs text-on-surface-variant">
                  No trending data
                </div>
              ) : (
                trending.map((t, i) => {
                  const change = t.token_price_change_24h ?? t.price_change_24h;
                  const changeNum = change != null ? Number(change) : null;
                  return (
                    <div key={i} className="glass rounded-xl p-4 border border-outline-variant/10">
                      <div className="font-bold text-sm mb-1 truncate">{t.symbol || t.name || 'Token'}</div>
                      <div className="font-mono text-[10px] text-on-surface-variant truncate">
                        {shortAddr(t.token || t.address || '')}
                      </div>
                      {t.current_price_usd && (
                        <div className="text-[11px] text-on-surface-variant mt-1">
                          ${Number(t.current_price_usd).toPrecision(3)}
                        </div>
                      )}
                      {changeNum != null && Number.isFinite(changeNum) && (
                        <div className={`text-xs font-bold mt-2 ${changeNum >= 0 ? 'text-success' : 'text-error'}`}>
                          {changeNum >= 0 ? '+' : ''}{changeNum.toFixed(1)}% 24h
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </section>
      </main>
    </>
  );
}

function computeRiskVerdict(risk) {
  if (!risk || typeof risk !== 'object') return 'UNKNOWN';
  const isHoneypot = risk.is_honeypot === true || risk.is_honeypot === 1 || risk.is_honeypot === 'true';
  const buyTax = Number(risk.buy_tax || 0);
  const sellTax = Number(risk.sell_tax || 0);
  if (isHoneypot) return 'BLOCK';
  if (buyTax > 10 || sellTax > 10) return 'WARN';
  return 'SAFE';
}

function SignalRow({ signal }) {
  const actionStyle = signal.action === 'OPEN'
    ? 'bg-success/10 text-success border-success/30'
    : 'bg-primary-container/10 text-primary-container border-primary-container/30';
  const riskStyle = signal.risk === 'BLOCK' ? 'verdict-REJECTED'
    : signal.risk === 'WARN' ? 'verdict-REVIEW'
    : signal.risk === 'SAFE' ? 'verdict-APPROVED'
    : '';

  const time = new Date(signal.at).toLocaleTimeString();

  return (
    <div className="glass rounded-xl px-5 py-3 border border-outline-variant/10 flex items-center gap-4 flex-wrap">
      <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-widest border ${actionStyle}`}>
        {signal.action}
      </span>
      <div className="flex-1 min-w-0">
        <div className="font-mono text-xs text-on-surface-variant">{shortAddr(signal.wallet)}</div>
        <div className="text-sm font-bold">{signal.token}</div>
      </div>
      <div className="text-xs text-on-surface-variant">{fmtUSD(signal.value_usd)}</div>
      {signal.risk && (
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest ${riskStyle}`}>
          {signal.risk}
        </span>
      )}
      <div className="text-[10px] text-on-surface-variant font-mono">{time}</div>
    </div>
  );
}
