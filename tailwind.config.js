/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        "teldem-blue": {
          DEFAULT: "#1B4F91",
          50: "#EAF1FA",
          100: "#CFE0F2",
          400: "#3B71B3",
          600: "#164079",
          700: "#123361",
          900: "#0B1F3A",
        },
        "teldem-green": {
          DEFAULT: "#2E9E44",
          50: "#EAF8ED",
          100: "#CDEFD5",
          600: "#258137",
          700: "#1F6B2E",
        },
        "teldem-gold": {
          DEFAULT: "#F5A623",
          50: "#FEF6E8",
          600: "#CC8615",
        },
        surface: "#F7F8FA",
        "surface-alt": "#EFF2F6",
        ink: "#1A1A1A",
        "ink-soft": "#333333",
        "ink-muted": "#5B6470",
      },
      fontFamily: {
        heading: ["Sora", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 24, 40, 0.06), 0 1px 3px rgba(16, 24, 40, 0.08)",
        "card-hover": "0 4px 8px rgba(16, 24, 40, 0.08), 0 2px 4px rgba(16, 24, 40, 0.06)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(to right, rgba(27,79,145,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(27,79,145,0.06) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "40px 40px",
      },
    },
  },
  plugins: [],
};
