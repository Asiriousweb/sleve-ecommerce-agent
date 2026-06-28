import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta dark estilo dashboard SLEVE
        ink: {
          950: "#0a0b0d",
          900: "#0f1115",
          850: "#14161c",
          800: "#181b22",
          700: "#22262f",
          600: "#2c313c",
        },
        accent: {
          up: "#34d399",   // verde (crece)
          down: "#f87171", // rojo (baja)
          brand: "#6ea8fe",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
