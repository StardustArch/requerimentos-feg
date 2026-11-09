/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        // Marca UCM: roxo do cabeçalho atual como brand-700, escala 50-900
        brand: {
          50: "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#2d2a8c",
          800: "#1e1a6b",
          900: "#161353",
        },
        // Neutros: slate
        slate: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
        // Semânticas por estado do requerimento
        estado: {
          novo: "#0ea5e9",      // sky-500
          credito: "#f59e0b",   // amber-500
          registo: "#8b5cf6",   // violet-500
          assinatura: "#f97316", // orange-500
          pronto: "#10b981",    // emerald-500
          indeferido: "#f43f5e", // rose-500
        },
      },
      borderRadius: {
        DEFAULT: "0.75rem", // rounded-xl
        sm: "0.5rem",       // rounded-md
        lg: "1rem",         // rounded-lg
        xl: "1rem",         // rounded-xl
        "2xl": "1.5rem",    // rounded-2xl
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        DEFAULT: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        hover: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      spacing: {
        "18": "4.5rem",
        "88": "22rem",
        "128": "32rem",
      },
      maxWidth: {
        "7xl": "80rem",
      },
    },
  },
  plugins: [],
}
