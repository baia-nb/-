/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        grass: '#5cb85c',
        'grass-dark': '#3b8526',
        dirt: '#7a5230',
        'panel': '#161b22',
        'panel-border': '#2b3340',
      },
      fontFamily: {
        pixel: ['"Press Start 2P"', 'monospace'],
        sans: ['"Noto Sans SC"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        block: '0 0 0 2px #0e1116, 0 8px 0 0 #0e1116',
      },
    },
  },
  plugins: [],
}
