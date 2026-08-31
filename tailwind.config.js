/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    '!./venv/**',
    '!./node_modules/**',
  ],
  theme: {
    extend: {
      colors: {
        brandBlue: '#008BC6',
        brandOrange: '#FF7200',
      },
      animation: {
        scaleIn: 'scaleIn 0.3s ease-out forwards',
        fadeIn: 'fadeIn 0.4s ease-out forwards',
        slideUp: 'slideUp 0.4s ease-out forwards',
        pulseGlow: 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0px rgba(0, 139, 198, 0.5)' },
          '50%': { boxShadow: '0 0 15px rgba(0, 139, 198, 0.8)' },
        },
        revealUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
