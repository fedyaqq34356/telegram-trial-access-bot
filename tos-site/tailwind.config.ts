import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#070611",
          soft: "#0d0b1a",
          card: "#13101f",
        },
        line: "rgba(255,255,255,0.08)",
        
        brand: {
          100: "#ece4ff",
          200: "#d8c6ff",
          300: "#c4a8ff",
          400: "#a982ff",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
        },
        
        neon: {
          300: "#ff9ad4",
          400: "#ff5fb6",
          500: "#ff2e9a",
          600: "#e01585",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(139,92,246,0.18), 0 24px 70px -24px rgba(124,58,237,0.55)",
        neon: "0 0 0 1px rgba(255,46,154,0.25), 0 18px 60px -22px rgba(255,46,154,0.5)",
        card: "0 18px 50px -28px rgba(0,0,0,0.85)",
      },
      borderRadius: { xl2: "1.25rem", xl3: "1.75rem" },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      keyframes: {
        floaty: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-12px)" } },
        pulseGlow: { "0%,100%": { opacity: "0.6" }, "50%": { opacity: "1" } },
      },
      animation: {
        floaty: "floaty 6s ease-in-out infinite",
        pulseGlow: "pulseGlow 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
