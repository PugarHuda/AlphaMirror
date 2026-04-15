export function fmtUSD(v, signed = false) {
  if (v == null) return '-';
  const n = Number(v);
  if (!Number.isFinite(n)) return '-';
  const abs = Math.abs(n);
  let s;
  if (abs >= 1_000_000) s = '$' + (n / 1_000_000).toFixed(2) + 'M';
  else if (abs >= 1_000) s = '$' + (n / 1_000).toFixed(1) + 'k';
  else s = '$' + n.toFixed(0);
  if (signed && n > 0) s = '+' + s;
  if (n < 0) s = s.replace('$', '-$').replace('--', '-');
  return s;
}

export function fmtPct(v) {
  if (v == null) return '-';
  const n = Number(v);
  if (!Number.isFinite(n)) return '-';
  const pct = n >= 0 && n <= 1 ? n * 100 : n;
  return pct.toFixed(0) + '%';
}

export function shortAddr(addr) {
  if (!addr) return '-';
  return addr.slice(0, 6) + '…' + addr.slice(-4);
}

export async function apiFetch(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}
