/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{vue,js,ts,jsx,tsx}", // Scan Vue, JS, and TS files for Tailwind classes
    "./src/*.{vue,js,ts,jsx,tsx}"  // Scan root src directory files as well
  ],
  theme: {
    extend: {}, // Add custom theme configurations here if needed
  },
  plugins: [],
}