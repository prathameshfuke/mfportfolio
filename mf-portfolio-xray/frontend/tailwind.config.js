/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0a0a0a',
        card: 'rgba(23,23,23,0.72)',
        teal: '#d4d4d4',
        amber: '#a3a3a3',
        warm: '#ffffff',
        danger: '#737373',
      },
      fontFamily: {
        body: ['DM Sans', 'sans-serif'],
        heading: ['Syne', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(82,82,82,0.35), 0 12px 28px rgba(0,0,0,0.35)',
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        rise: 'rise 500ms ease-out both',
      },
    },
  },
  plugins: [],
}
