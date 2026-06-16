import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#08070d",
          soft: "#0d0c16",
          sidebar: "#0a0910",
        },
        card: "rgba(22, 20, 35, 0.6)",
        line: "rgba(255,255,255,0.07)",
        brand: {
          50: "#f3effe",
          100: "#e6dcff",
          300: "#b79dff",
          400: "#9b7bff",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
        },
        ok: "#34d399",
        warn: "#fbbf24",
        danger: "#f43f5e",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(139,92,246,0.18), 0 18px 50px -20px rgba(124,58,237,0.45)",
        card: "0 12px 40px -24px rgba(0,0,0,0.8)",
      },
      borderRadius: { xl2: "1.1rem" },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
