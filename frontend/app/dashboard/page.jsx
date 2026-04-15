'use client';

import { useEffect, useState, useCallback } from 'react';
import Nav from '@/components/Nav';
import WalletCard from '@/components/WalletCard';
import WalletModal from '@/components/WalletModal';
import TokenModal from '@/components/TokenModal';
import MirrorModal from '@/components/MirrorModal';
import { apiFetch } from '@/lib/format';

export default function DashboardPage() {
  const [chain, setChain] = useState('bsc');
  const [topN, setTopN] = useState(5);
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [apiOk, setApiOk] = useState(true);

  // Modals
  const [walletModal, setWalletModal] = useState(null); // { chain, address }
  const [tokenModal, setTokenModal] = useState(null);   // { chain, address }
  const [mirrorModal, setMirrorModal] = useState(null); // wallet object

  // Health check on mount
  useEffect(() => {
    apiFetch('/api/health')
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));
  }, []);

  const runPipeline = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResults(null);
    setProgress(5);
    setProgressLabel('Phase 1: discovering candidates...');

    // Asymptotic progress simulation so the bar feels alive
    const estMs = (1 + topN * 2) * 1000;
    const start = Date.now();
    const timer = setInterval(() => {
      const elapsed = Date.now() - start;
      const pct = 90 * (1 - Math.exp(-elapsed / (estMs / 2.5)));
      setProgress(pct);
      setProgressLabel(`Phase 2: verifying wallets (~${Math.round(elapsed / 1000)}s)`);
    }, 200);

    try {
      const q = new URLSearchParams({ chain, top: String(topN) });
      if (keyword) q.set('keyword', keyword);
      const data = await apiFetch(`/api/pipeline?${q.toString()}`);
      setResults(data);
      setProgress(100);
      setProgressLabel('Complete');
    } catch (err) {
      setError(err.message);
    } finally {
      clearInterval(timer);
      setLoading(false);
      setTimeout(() => setProgress(0), 800);
    }
  }, [chain, topN, keyword]);

  const summary = results?.summary || { approved: 0, review: 0, rejected: 0 };

  return (
    <>
      <Nav />
      <main className="max-w-[1600px] mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6 min-h-[calc(100vh-4rem)]">

        {/* Sidebar */}
        <aside className="h-fit space-y-5 lg:sticky lg:top-24">
          <div className="glass rounded-2xl p-6 border border-outline-variant/10">
            <h3 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label mb-5">
              Pipeline Controls
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
              <div className="flex justify-between mb-2">
                <span className="text-xs text-on-surface-variant font-label font-semibold">
                  Candidates to verify
                </span>
                <span className="text-xs text-primary-container font-bold font-mono">{topN}</span>
              </div>
              <input
                type="range"
                min="3"
                max="15"
                value={topN}
                onChange={(e) => setTopN(parseInt(e.target.value, 10))}
                className="w-full accent-primary-container"
              />
            </label>

            <label className="block mb-5">
              <div className="text-xs text-on-surface-variant mb-2 font-label font-semibold">
                Keyword (optional)
              </div>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="e.g. PEPE"
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2.5 text-sm font-medium focus:border-primary-container focus:outline-none"
              />
            </label>

            <button
              onClick={runPipeline}
              disabled={loading}
              className="w-full py-3 bg-primary-container text-on-primary rounded-xl font-bold hover:brightness-110 transition flex items-center justify-center gap-2 disabled:opacity-60"
            >
              <span className={`material-symbols-outlined ${loading ? 'animate-spin' : ''}`}>
                {loading ? 'progress_activity' : 'play_arrow'}
              </span>
              {loading ? 'Running...' : 'Run Pipeline'}
            </button>

            <div className="mt-4 pt-4 border-t border-outline-variant/10 text-xs text-on-surface-variant leading-relaxed">
              <div className="flex items-start gap-2">
                <span className="material-symbols-outlined text-sm mt-0.5">info</span>
                <span>Free tier runs at 1 TPS. Verifying 5 wallets takes ~12s.</span>
              </div>
            </div>
          </div>

          <div className="glass rounded-2xl p-6 border border-outline-variant/10">
            <h3 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant font-label mb-4">
              API Status
            </h3>
            <div className="flex items-center gap-2 text-sm">
              <span className={`w-2 h-2 rounded-full ${apiOk ? 'bg-success animate-pulse' : 'bg-error'}`} />
              <span className={apiOk ? 'text-on-surface' : 'text-error'}>
                {apiOk ? 'Backend connected' : 'Backend offline'}
              </span>
            </div>
            <div className="mt-3 text-[11px] text-on-surface-variant">
              <div>FastAPI on port 8000</div>
              <div className="font-mono mt-1">
                {apiOk ? '12/12 AVE endpoints' : 'run: python server.py'}
              </div>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <section className="space-y-6">
          <div className="glass rounded-2xl p-6 border border-outline-variant/10 relative overflow-hidden">
            <div className="absolute inset-0 grid-bg pointer-events-none opacity-60" />
            <div className="relative">
              <h1 className="text-2xl font-extrabold mb-1">Smart Money Verification</h1>
              <p className="text-on-surface-variant text-sm mb-6">
                AVE classifies candidates. AlphaMirror verifies them against 6 independent signals.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <MetricCard label="Verified" value={results?.count ?? '-'} />
                <MetricCard label="Approved" value={summary.approved} color="success" />
                <MetricCard label="Review" value={summary.review} color="primary-container" />
                <MetricCard label="Rejected" value={summary.rejected} color="error" />
              </div>
            </div>
          </div>

          {/* Progress */}
          {(loading || progress > 0) && (
            <div className="glass rounded-2xl p-6 border border-primary-container/20 fade-in">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary-container animate-spin">progress_activity</span>
                  <div className="text-sm font-semibold">{progressLabel}</div>
                </div>
                <div className="text-xs font-mono text-primary-container font-bold">{Math.round(progress)}%</div>
              </div>
              <div className="h-2 bg-surface-container-low rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-container to-primary-container/60 transition-all duration-300 pulse-glow"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="mt-3 text-xs text-on-surface-variant">
                {loading ? 'Calling AVE endpoints...' : 'Finalizing results...'}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="glass rounded-2xl p-8 border border-error/30 bg-error/5">
              <div className="flex items-start gap-4">
                <span className="material-symbols-outlined text-error text-3xl">error</span>
                <div>
                  <h3 className="font-bold text-error mb-1">Pipeline failed</h3>
                  <code className="text-xs text-on-surface-variant font-mono break-all">{error}</code>
                </div>
              </div>
            </div>
          )}

          {/* Empty */}
          {!loading && !results && !error && (
            <div className="glass rounded-2xl p-16 border border-outline-variant/10 text-center fade-in">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-primary-container/10 mb-6">
                <span className="material-symbols-outlined text-5xl text-primary-container">bolt</span>
              </div>
              <h2 className="text-2xl font-bold mb-3">Ready to verify smart money</h2>
              <p className="text-on-surface-variant text-sm max-w-md mx-auto mb-6 leading-relaxed">
                Click <span className="text-primary-container font-bold">Run Pipeline</span> in the sidebar to
                discover and verify smart-money wallets on the selected chain. The verification layer will
                cross-check AVE's candidates against 6 independent quality signals.
              </p>
              <div className="flex items-center justify-center gap-8 text-xs text-on-surface-variant">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-success">check_circle</span>
                  <span>6 quality signals</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-success">check_circle</span>
                  <span>One-hit wonder detector</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-success">check_circle</span>
                  <span>Free tier compatible</span>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {results && results.wallets && (
            <div className="space-y-4">
              {results.wallets.length === 0 ? (
                <div className="glass rounded-2xl p-16 border border-outline-variant/10 text-center fade-in">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-error/10 mb-6">
                    <span className="material-symbols-outlined text-5xl text-error">search_off</span>
                  </div>
                  <h2 className="text-2xl font-bold mb-3">No candidates returned</h2>
                  <p className="text-on-surface-variant text-sm mt-2 max-w-md mx-auto mb-6">
                    AVE's smart_wallets endpoint didn't return any candidates for this configuration.
                    Try a different chain or remove the keyword filter.
                  </p>
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={() => setKeyword('')}
                      className="px-4 py-2 bg-surface-container-high hover:bg-surface-container-highest rounded-lg text-sm font-bold"
                    >
                      Clear keyword
                    </button>
                    <button
                      onClick={() => setChain(chain === 'bsc' ? 'eth' : 'bsc')}
                      className="px-4 py-2 bg-primary-container/20 hover:bg-primary-container/30 text-primary-container border border-primary-container/30 rounded-lg text-sm font-bold"
                    >
                      Try {chain === 'bsc' ? 'Ethereum' : 'BSC'}
                    </button>
                  </div>
                </div>
              ) : (
                results.wallets.map((w, i) => (
                  <WalletCard
                    key={w.address}
                    wallet={w}
                    rank={i + 1}
                    onDrillDown={() => setWalletModal({ chain: w.chain, address: w.address })}
                    onMirror={() => setMirrorModal(w)}
                  />
                ))
              )}
            </div>
          )}
        </section>
      </main>

      {walletModal && (
        <WalletModal
          chain={walletModal.chain}
          address={walletModal.address}
          onClose={() => setWalletModal(null)}
          onTokenClick={(tokenChain, tokenAddr) => setTokenModal({ chain: tokenChain, address: tokenAddr })}
        />
      )}
      {tokenModal && (
        <TokenModal
          chain={tokenModal.chain}
          address={tokenModal.address}
          onClose={() => setTokenModal(null)}
        />
      )}
      {mirrorModal && (
        <MirrorModal wallet={mirrorModal} onClose={() => setMirrorModal(null)} />
      )}
    </>
  );
}

function MetricCard({ label, value, color }) {
  const borderClass = color === 'success' ? 'border-success/30'
    : color === 'primary-container' ? 'border-primary-container/30'
    : color === 'error' ? 'border-error/30'
    : 'border-outline-variant/10';
  const textClass = color === 'success' ? 'text-success'
    : color === 'primary-container' ? 'text-primary-container'
    : color === 'error' ? 'text-error'
    : 'text-on-surface';
  return (
    <div className={`bg-surface-container-low rounded-xl p-4 border ${borderClass}`}>
      <div className={`text-xs font-label font-semibold mb-1 ${textClass}`}>{label}</div>
      <div className={`text-2xl font-extrabold ${textClass}`}>{value}</div>
    </div>
  );
}
