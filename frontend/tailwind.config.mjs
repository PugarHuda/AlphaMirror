/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './app/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'surface': '#131313',
        'surface-bright': '#393939',
        'surface-container': '#201f1f',
        'surface-container-low': '#1c1b1b',
        'surface-container-lowest': '#0e0e0e',
        'surface-container-high': '#2a2a2a',
        'surface-container-highest': '#353534',
        'outline': '#a78b7c',
        'outline-variant': '#584235',
        'on-surface': '#e5e2e1',
        'on-surface-variant': '#e0c0af',
        'primary': '#ffb68b',
        'primary-container': '#ff7a00',
        'on-primary': '#522300',
        'secondary': '#ffb68b',
        'tertiary': '#95ccff',
        'tertiary-container': '#00a8ff',
        'error': '#ffb4ab',
        'success': '#7dd08a',
      },
      fontFamily: {
        headline: ['Manrope', 'sans-serif'],
        body: ['Manrope', 'sans-serif'],
        label: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
