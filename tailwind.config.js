/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html"],
  theme: { extend: {
    colors: {
      charcoal: "#1F2937",
      fog: "#E5E7EB",
      accent: { blue: "#3B82F6", green: "#10B981", red: "#EF4444" }
    },
    borderRadius: { xl: "1rem", "2xl": "1.5rem" },
  }},
  plugins: [],
};
