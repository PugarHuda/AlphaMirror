import './globals.css';

export const metadata = {
  title: 'AlphaMirror — Verified Smart-Money Copy-Trading',
  description: 'Non-custodial copy-trading agent built on AVE Cloud Skill. Verify smart money with 12 endpoints across 2 skills.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
