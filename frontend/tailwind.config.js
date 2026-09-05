/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EDE7DD",
        "paper-light": "#F7F3EC",
        ink: "#2B2A28",
        "ink-muted": "#6B675F",
        teal: "#2F5D57",
        gold: "#C99A3C",
        "gold-light": "#F1E4C6",
        rose: "#B8604C",
      },
      fontFamily: {
        serif: ["Fraunces", "Georgia", "serif"],
        sans: ["Work Sans", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
