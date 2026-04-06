import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12162B",
        mist: "#F2F5FF",
        lilac: "#E7D8FF",
        peach: "#FFE4D6",
        cloud: "#F8F9FF",
        line: "rgba(94, 102, 148, 0.12)",
      },
      boxShadow: {
        soft: "0 22px 70px rgba(147, 135, 255, 0.16)",
        glow: "0 20px 60px rgba(255, 176, 220, 0.22)",
        panel: "0 24px 80px rgba(38, 44, 92, 0.10)",
      },
      backgroundImage: {
        aurora:
          "radial-gradient(circle at 20% 20%, rgba(166,220,255,0.7), transparent 26%), radial-gradient(circle at 78% 18%, rgba(255,212,238,0.7), transparent 24%), radial-gradient(circle at 52% 84%, rgba(198,182,255,0.5), transparent 28%), linear-gradient(135deg, #f7f7ff 0%, #fff6fb 50%, #f5fbff 100%)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
