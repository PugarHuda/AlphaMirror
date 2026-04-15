'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Nav() {
  const path = usePathname();
  const is = (p) => (path === p ? 'text-primary-container font-bold border-b-2 border-primary-container pb-1' : 'text-on-surface-variant font-medium hover:text-on-surface transition');

  return (
    <nav className="sticky top-0 z-50 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10">
      <div className="flex justify-between items-center max-w-[1600px] mx-auto px-8 h-16">
        <Link href="/" className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-primary-container flex items-center justify-center">
            <span className="material-symbols-outlined text-on-primary text-lg">diamond</span>
          </div>
          <div className="text-base font-extrabold tracking-tight">AlphaMirror</div>
        </Link>
        <div className="hidden md:flex items-center gap-6 text-sm">
          <Link href="/" className={is('/')}>Home</Link>
          <Link href="/dashboard" className={is('/dashboard')}>Dashboard</Link>
          <Link href="/monitor" className={is('/monitor')}>Monitor</Link>
          <a
            href="https://github.com/PugarHuda/AlphaMirror"
            target="_blank"
            rel="noreferrer"
            className="text-on-surface-variant font-medium hover:text-on-surface transition"
          >
            GitHub
          </a>
        </div>
        <Link
          href="/dashboard"
          className="bg-primary-container text-on-primary font-bold px-4 py-2 rounded-xl hover:scale-95 duration-200 transition-transform text-xs"
        >
          Launch App
        </Link>
      </div>
    </nav>
  );
}
