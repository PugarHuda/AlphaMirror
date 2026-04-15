import Nav from '@/components/Nav';
import Link from 'next/link';

const AVE_ENDPOINTS = [
  'smart_wallets',
  'wallet_info',
  'wallet_tokens',
  'address_pnl',
  'address_txs',
  'risk',
  'token',
  'kline_token',
  'holders',
  'txs',
  'trending',
  'search',
];

export default function HomePage() {
  return (
    <>
      <Nav />

      <main>
        {/* Hero */}
        <section className="relative min-h-screen flex flex-col items-center justify-center pt-32 pb-20 px-8 overflow-hidden">
          <div className="absolute inset-0 z-0 grid-bg" />
          <div className="absolute inset-0 z-0 radial-fade" />

          <div className="relative z-10 text-center max-w-5xl mx-auto mb-20">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-container/10 border border-primary-container/20 mb-8">
              <span className="w-2 h-2 bg-primary-container rounded-full animate-pulse" />
              <span className="text-primary-container text-xs font-bold uppercase tracking-widest">
                AVE Claw Hackathon 2026
              </span>
            </div>
            <h1 className="font-headline text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-[1.05]">
              Copy-trade smart money.
              <br />
              <span className="text-primary-container text-glow">Only the ones that are actually smart.</span>
            </h1>
            <p className="font-body text-xl text-on-surface-variant max-w-3xl mx-auto mb-12 leading-relaxed">
              Most &ldquo;smart money&rdquo; wallets on Twitter are actually unprofitable. AlphaMirror cross-checks
              AVE Cloud&apos;s classification against{' '}
              <span className="text-on-surface font-semibold">six independent quality signals</span> and rejects
              the one-hit wonders before you ever copy a trade.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/dashboard"
                className="w-full sm:w-auto px-8 py-4 bg-primary-container text-on-primary rounded-xl font-bold text-lg hover:brightness-110 transition flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined">rocket_launch</span>
                Launch Dashboard
              </Link>
              <Link
                href="/monitor"
                className="w-full sm:w-auto px-8 py-4 border border-outline-variant/30 text-on-surface rounded-xl font-bold text-lg hover:bg-surface-container-low transition flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined">radar</span>
                Live Monitor
              </Link>
            </div>
          </div>

          {/* Stats */}
          <div className="relative z-10 w-full max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat value="12" label="AVE Endpoints" />
            <Stat value="4" label="Chains" />
            <Stat value="6" label="Quality Signals" />
            <Stat value="0" label="Private Keys Held" />
          </div>
        </section>

        {/* Problem */}
        <section className="py-24 bg-surface-container-lowest">
          <div className="max-w-5xl mx-auto px-8">
            <div className="text-center mb-16">
              <div className="inline-block px-4 py-1.5 rounded-full bg-error/10 border border-error/20 text-error text-xs font-bold uppercase tracking-widest mb-6">
                The Problem
              </div>
              <h2 className="font-headline text-3xl md:text-5xl font-extrabold mb-6">
                &ldquo;Smart money&rdquo; is a label, not a verdict.
              </h2>
              <p className="text-on-surface-variant text-lg max-w-3xl mx-auto">
                Copy-trading platforms rank wallets by raw profit. Three systemic failures follow.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <ProblemCard
                icon="casino"
                title="One-hit wonders dominate"
                body="A wallet with one lucky 100x trade shows the same total profit as a wallet with twenty consistent 2-5x wins. Retail can't tell them apart from the leaderboard."
              />
              <ProblemCard
                icon="bedtime"
                title="Dormant whales get followed"
                body="Wallets profitable a year ago still appear on top even if they haven't traded in 90 days. Recency signal is missing."
              />
              <ProblemCard
                icon="trending_down"
                title="'Smart' wallets lose money"
                body="Even AVE's own classifier returns wallets that are net negative when you check the numbers. A candidate pool is not a verdict."
              />
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="py-32 bg-surface">
          <div className="max-w-7xl mx-auto px-8">
            <div className="text-center mb-20">
              <div className="inline-block px-4 py-1.5 rounded-full bg-primary-container/10 border border-primary-container/20 text-primary-container text-xs font-bold uppercase tracking-widest mb-6">
                How it works
              </div>
              <h2 className="font-headline text-4xl md:text-5xl font-extrabold mb-4">
                Verification, not just discovery.
              </h2>
              <p className="text-on-surface-variant text-lg max-w-2xl mx-auto">
                Five phases, twelve AVE endpoints, one clean verdict per wallet.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <PhaseCard
                num="01"
                icon="search"
                title="Discover"
                body="Pull smart-money candidates from smart_wallets, AVE's built-in classifier."
              />
              <PhaseCard
                num="02"
                icon="verified"
                title="Verify"
                body="Cross-check each candidate against six signals. APPROVED / REVIEW / REJECTED verdicts."
              />
              <PhaseCard
                num="03"
                icon="radar"
                title="Monitor"
                body="Poll approved wallets for new positions. Automatic honeypot check before any alert."
              />
              <PhaseCard
                num="04"
                icon="swap_horiz"
                title="Mirror"
                body="Self-custody quote via trade-chain-wallet. You sign in your own wallet. Zero custody."
              />
            </div>
          </div>
        </section>

        {/* AVE endpoints */}
        <section className="py-32 bg-surface-container-lowest">
          <div className="max-w-6xl mx-auto px-8">
            <div className="text-center mb-16">
              <div className="inline-block px-4 py-1.5 rounded-full bg-primary-container/10 border border-primary-container/20 text-primary-container text-xs font-bold uppercase tracking-widest mb-6">
                Deep Integration
              </div>
              <h2 className="font-headline text-4xl md:text-5xl font-extrabold mb-4">
                12 endpoints, 2 AVE Skills, 100% utilization.
              </h2>
              <p className="text-on-surface-variant text-lg max-w-2xl mx-auto">
                Every AVE Cloud endpoint we expose is actively called in the runtime flow, not just declared.
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-4xl mx-auto font-mono text-sm">
              {AVE_ENDPOINTS.map((e) => (
                <div key={e} className="glass p-4 rounded-xl border border-outline-variant/10 flex items-center gap-3">
                  <span className="material-symbols-outlined text-success text-lg">check_circle</span>
                  <code>{e}</code>
                </div>
              ))}
            </div>
            <div className="text-center mt-8 text-on-surface-variant text-sm">
              Plus <code className="text-primary-container font-mono">trade-chain-wallet quote</code> for non-custodial mirror trades.
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-32 px-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-primary-container" />
          <div className="relative z-10 max-w-4xl mx-auto text-center">
            <h2 className="font-headline text-4xl md:text-6xl font-extrabold text-on-primary mb-6 leading-tight">
              Stop mirroring unprofitable wallets.
            </h2>
            <p className="text-on-primary/80 text-xl mb-12 max-w-2xl mx-auto font-medium">
              Run the pipeline yourself. See how many &ldquo;smart money&rdquo; wallets our verification layer rejects.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/dashboard"
                className="w-full sm:w-auto px-10 py-4 bg-on-primary text-primary-container rounded-2xl font-black text-lg hover:scale-105 transition shadow-2xl"
              >
                Open Dashboard
              </Link>
              <Link
                href="/monitor"
                className="w-full sm:w-auto px-10 py-4 border-2 border-on-primary/20 text-on-primary rounded-2xl font-bold text-lg hover:bg-on-primary/5 transition"
              >
                Live Monitor
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-surface-container-lowest w-full border-t border-outline-variant/10">
        <div className="max-w-7xl mx-auto py-10 px-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primary-container flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary text-base">diamond</span>
            </div>
            <div className="font-bold">AlphaMirror</div>
          </div>
          <div className="flex flex-wrap justify-center gap-8 text-sm">
            <a href="https://github.com/PugarHuda/AlphaMirror" target="_blank" rel="noreferrer" className="text-on-surface-variant hover:text-primary-container transition">GitHub</a>
            <a href="https://cloud.ave.ai" target="_blank" rel="noreferrer" className="text-on-surface-variant hover:text-primary-container transition">AVE Cloud</a>
            <Link href="/dashboard" className="text-on-surface-variant hover:text-primary-container transition">Dashboard</Link>
            <Link href="/monitor" className="text-on-surface-variant hover:text-primary-container transition">Monitor</Link>
          </div>
          <p className="text-on-surface-variant text-xs font-label text-center md:text-right">
            Built for AVE Claw Hackathon 2026
            <br />
            Non-custodial by design
          </p>
        </div>
      </footer>
    </>
  );
}

function Stat({ value, label }) {
  return (
    <div className="glass rounded-2xl p-6 border border-outline-variant/10 text-center">
      <div className="text-4xl font-extrabold text-primary-container mb-1">{value}</div>
      <div className="text-xs text-on-surface-variant uppercase tracking-widest font-bold">{label}</div>
    </div>
  );
}

function ProblemCard({ icon, title, body }) {
  return (
    <div className="glass p-8 rounded-2xl border border-outline-variant/10">
      <div className="w-12 h-12 bg-error/10 rounded-xl flex items-center justify-center mb-5">
        <span className="material-symbols-outlined text-error text-3xl">{icon}</span>
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-on-surface-variant text-sm leading-relaxed">{body}</p>
    </div>
  );
}

function PhaseCard({ num, icon, title, body }) {
  return (
    <div className="glass p-6 rounded-2xl border border-outline-variant/10 hover:border-primary-container/30 transition group">
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 bg-surface-container-high rounded-xl flex items-center justify-center group-hover:scale-110 transition">
          <span className="material-symbols-outlined text-primary-container text-2xl">{icon}</span>
        </div>
        <span className="text-xs font-bold text-on-surface-variant">{num}</span>
      </div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-on-surface-variant text-sm leading-relaxed">{body}</p>
    </div>
  );
}
