/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Background layers
        bg: {
          0: '#0a0a12',
          1: '#0e0e1a',
          2: '#12121f',
          3: '#17172a',
          4: '#1e1e35',
          5: '#252545',
        },
        // Borders
        border: {
          1: 'rgba(255,255,255,0.07)',
          2: 'rgba(255,255,255,0.12)',
        },
        // Text
        ink: {
          1: '#f0f0f8',
          2: '#c0c0d8',
          3: '#7878a0',
          4: '#4a4a70',
        },
        // Accent - indigo
        accent: {
          DEFAULT: '#6366f1',
          light: '#818cf8',
          dim: 'rgba(99,102,241,0.15)',
          border: 'rgba(99,102,241,0.3)',
        },
        // Semantic
        em: {
          green: '#10b981',
          orange: '#f97316',
          red: '#ef4444',
          amber: '#f59e0b',
          yellow: '#fbbf24',
          blue: '#3b82f6',
          purple: '#8b5cf6',
          pink: '#ec4899',
          teal: '#14b8a6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'Consolas', 'monospace'],
      },
      borderRadius: {
        'sm': '6px',
        'md': '10px',
        'lg': '14px',
        'xl': '18px',
        '2xl': '24px',
      },
      boxShadow: {
        'glow-accent': '0 0 20px rgba(99,102,241,0.25)',
        'glow-green': '0 0 20px rgba(16,185,129,0.25)',
        'glow-sm': '0 0 8px rgba(99,102,241,0.2)',
        'card': '0 4px 24px rgba(0,0,0,0.4)',
        'card-hover': '0 8px 32px rgba(0,0,0,0.5)',
      },
      backgroundImage: {
        'grad-accent': 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        'grad-green': 'linear-gradient(135deg, #10b981, #14b8a6)',
        'grad-orange': 'linear-gradient(135deg, #f97316, #fbbf24)',
        'grad-blue': 'linear-gradient(135deg, #3b82f6, #6366f1)',
        'sidebar-fade': 'linear-gradient(180deg, rgba(99,102,241,0.04) 0%, transparent 40%)',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 4px rgba(16,185,129,0.4)' },
          '50%': { boxShadow: '0 0 14px rgba(16,185,129,0.8)' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          from: { opacity: '0', transform: 'translateX(-8px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'fade-up': 'fade-up 0.2s ease',
        'slide-in': 'slide-in 0.2s ease',
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
}
