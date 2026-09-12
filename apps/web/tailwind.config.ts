import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        paper: "rgb(var(--color-paper) / <alpha-value>)",
        brass: "rgb(var(--color-brass) / <alpha-value>)",
        sage: "rgb(var(--color-sage) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        scrim: "rgb(var(--color-scrim) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
