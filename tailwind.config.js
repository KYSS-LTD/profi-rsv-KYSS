/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: 'var(--tg-bg-color, #f4f7fb)',
          text: 'var(--tg-text-color, #172033)',
          hint: 'var(--tg-hint-color, #667085)',
          link: 'var(--tg-link-color, #2481cc)',
          button: 'var(--tg-button-color, #2481cc)',
          buttonText: 'var(--tg-button-text-color, #ffffff)',
          secondaryBg: 'var(--tg-secondary-bg-color, #ffffff)',
        },
      },
      boxShadow: {
        soft: '0 18px 50px rgba(16, 24, 40, 0.08)',
      },
    },
  },
  plugins: [],
};
