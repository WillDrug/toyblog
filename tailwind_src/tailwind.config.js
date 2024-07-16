/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["*.html"],
  theme: {
    extend: {},
  },
  plugins: [],
  safelist: [
    {
      pattern: /[mp][lrbt]?-[1-9][0-9]?/,
    },
  ],
}

// npx tailwindcss -i ./src/input.css -o ./src/output.css --watch