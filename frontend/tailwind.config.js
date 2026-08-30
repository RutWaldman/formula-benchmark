/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors for benchmark methods
        dotnet: {
          DEFAULT: '#512BD4',
          light: '#7B4FE0',
        },
        python: {
          DEFAULT: '#3776AB',
          light: '#5A9FD4',
        },
        sql: {
          DEFAULT: '#F29111',
          light: '#FFB347',
        },
      },
    },
  },
  plugins: [],
}
