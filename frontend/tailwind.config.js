/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Inter Tight', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
        title: ['clamp(1.625rem, 1.2rem + 1.5vw, 2.125rem)', { lineHeight: '1.1', letterSpacing: '-0.03em' }],
        display: ['clamp(2.5rem, 1.5rem + 3.4vw, 3.75rem)', { lineHeight: '1', letterSpacing: '-0.04em' }],
        'display-xl': ['clamp(3rem, 1.7rem + 4.4vw, 4.5rem)', { lineHeight: '0.98', letterSpacing: '-0.045em' }],
      },
      colors: {
        brand: {
          50: '#eff5ff',
          100: '#dbe8fe',
          200: '#bfd7fe',
          300: '#93bbfd',
          400: '#6098fa',
          500: '#3b76f6',
          600: '#2563eb',
          700: '#1d56d2',
          800: '#1e46aa',
          900: '#1e3e86',
          950: '#172a52',
        },
        accent: {
          50: '#ecfeff',
          100: '#cffafe',
          200: '#a5f0fb',
          300: '#67e3f5',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
        },
      },
      boxShadow: {
        soft: '0 24px 80px rgba(15, 23, 42, 0.08)',
        card: '0 1px 2px -1px rgba(16, 24, 40, 0.06), 0 2px 6px -2px rgba(16, 24, 40, 0.06)',
        elevated:
          'inset 0 1px 0 0 rgba(255, 255, 255, 0.6), 0 1px 2px -1px rgba(16, 24, 40, 0.05), 0 8px 20px -10px rgba(16, 24, 40, 0.14)',
        'card-hover':
          'inset 0 1px 0 0 rgba(255, 255, 255, 0.7), 0 6px 14px -6px rgba(16, 24, 40, 0.10), 0 22px 44px -16px rgba(16, 24, 40, 0.22)',
        brand: '0 14px 30px -8px rgba(37, 99, 235, 0.50)',
        'brand-sm': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.22), 0 6px 16px -5px rgba(37, 99, 235, 0.45)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #2563eb 0%, #22d3ee 100%)',
        'brand-gradient-dark': 'linear-gradient(135deg, #1e3e86 0%, #2563eb 55%, #22d3ee 130%)',
        'brand-button': 'linear-gradient(180deg, #3b76f6 0%, #2563eb 100%)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.98)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'pulse-ring': {
          '0%': { boxShadow: '0 0 0 0 rgba(16, 185, 129, 0.5)' },
          '70%': { boxShadow: '0 0 0 6px rgba(16, 185, 129, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(16, 185, 129, 0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease both',
        'fade-up': 'fade-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both',
        'scale-in': 'scale-in 0.3s ease both',
        'pulse-ring': 'pulse-ring 2s ease-out infinite',
      },
    },
  },
  plugins: [],
};
