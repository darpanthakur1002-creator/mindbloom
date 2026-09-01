/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./App.tsx', './src/**/*.{js,jsx,ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        primary: '#0f5238',
        'primary-container': '#2d6a4f',
        'primary-fixed': '#b1f0ce',
        surface: '#fbf8ff',
        'surface-container': '#ececff',
        'surface-container-low': '#f4f2ff',
        'surface-container-high': '#e5e6ff',
        'on-surface': '#161a32',
        'on-surface-variant': '#404943',
        lavender: '#eedbff',
        rose: '#ffd8e9',
      },
    },
  },
  plugins: [],
};
