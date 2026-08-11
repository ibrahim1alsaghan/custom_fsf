/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fsf: {
          primary: '#374736',
          'primary-dark': '#2A3629',
          secondary: '#C5A470',
          text: '#1d2125',
          'text-muted': '#5f6368',
          bg: '#f8f9fa',
          border: '#e0e0e0',
        }
      },
      fontFamily: {
        arabic: ['IBM Plex Sans Arabic', 'sans-serif'],
      },
      container: {
        center: true,
        padding: {
          DEFAULT: '1rem',
          sm: '2rem',
          lg: '4rem',
          xl: '5rem',
        },
      },
    },
  },
  plugins: [],
}
