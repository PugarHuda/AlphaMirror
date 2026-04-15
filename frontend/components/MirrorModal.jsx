'use client';

import { useState } from 'react';
import { apiFetch, fmtUSD, shortAddr } from '@/lib/format';

export default function MirrorModal({ wallet, onClose }) {
  const holdings = (wallet.holdings || []).filter((h) => !h.is_blue_chip && h.token_address);
  const [tokenAddr, setTokenAddr] = useState(holdings[0]?.token_address || '');
  const [usd, setUsd] = useState(50);
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const buildQuote = async () => {
    setLoading(true);
    setError(null);
    setQuote(null);
    const decimals = wallet.chain === 'eth' || wallet.chain === 'base' ? 6 : 18;
    try {
      const data = await apiFetch('/api/mirror', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chain: wallet.chain, token: tokenAddr, usd, decimals }),
      });
      setQuote(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyCommand = async () => {
    if (!quote?.command) return;
    await navigator.clipboard.writeText(quote.command);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur" onClick={onClose}>
      <div
        className="glass border border-primary-container/30 rounded-3xl max-w-2xl w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-outline-variant/10 flex items-center justify-between">
          <div>
            <div className="text-xs text-primary-container uppercase tracking-widest font-label font-bold">
              Self-Custody Mirror
            </div>
            <div className="font-bold mt-0.5">Your keys never leave your wallet</div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-surface-container-high rounded-lg">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="text-sm text-on-surface-variant">
            Mirror a trade from <span className="font-mono text-on-surface">{shortAddr(wallet.address)}</span>.
            We build the AVE{' '}
            <code className="text-primary-container font-mono">trade-chain-wallet quote</code> command — you sign
            in your own wallet.
          </div>

          <label className="block">
            <div className="text-xs text-on-surface-variant mb-2 font-label font-semibold uppercase tracking-widest">
              Token to mirror
            </div>
            <select
              value={tokenAddr}
              onChange={(e) => setTokenAddr(e.target.value)}
              className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2.5 text-sm font-medium focus:border-primary-container focus:outline-none"
            >
              {holdings.length === 0 ? (
                <option value="">No non-bluechip holdings</option>
              ) : (
                holdings.map((h) => (
                  <option key={h.token_address} value={h.token_address}>
                    {h.symbol} ({fmtUSD(h.balance_usd)})
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="block">
            <div className="text-xs text-on-surface-variant mb-2 font-label font-semibold uppercase tracking-widest">
              Mirror size (USD)
            </div>
            <input
              type="number"
              min="10"
              max="500"
              step="10"
              value={usd}
              onChange={(e) => setUsd(parseFloat(e.target.value))}
              className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2.5 text-sm font-medium focus:border-primary-container focus:outline-none"
            />
          </label>

          <button
            onClick={buildQuote}
            disabled={loading || !tokenAddr}
            className="w-full py-3 bg-primary-container text-on-primary rounded-xl font-bold hover:brightness-110 transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <span className={`material-symbols-outlined ${loading ? 'animate-spin' : ''}`}>
              {loading ? 'progress_activity' : 'construction'}
            </span>
            {loading ? 'Building...' : 'Build self-custody quote'}
          </button>

          {error && <div className="text-error text-sm">{error}</div>}

          {quote && (
            <div className="bg-surface-container-low rounded-xl p-4 border border-success/30">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-success">check_circle</span>
                <span className="font-bold text-success text-sm">Quote ready — copy and run in your terminal</span>
              </div>
              <pre className="text-[11px] font-mono text-on-surface-variant overflow-x-auto scroll-area bg-surface-container-lowest p-3 rounded-lg whitespace-pre-wrap break-all">
                {quote.command}
              </pre>
              <button
                onClick={copyCommand}
                className="mt-2 text-xs text-primary-container font-bold hover:underline"
              >
                {copied ? '✓ Copied' : 'Copy to clipboard'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
