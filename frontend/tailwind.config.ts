import type { Config } from "tailwindcss";

/**
 * Deep Tech Luminance — the design system in frontend/Images/Image 9.markdown.
 *
 * The token names are Material 3's (surface, on-surface, surface-container-*,
 * primary / on-primary / primary-container). They are copied verbatim from the
 * spec rather than renamed to something friendlier, because the three HTML
 * reference pages in that directory are written against these exact class
 * names and any rename makes them unusable as a reference.
 *
 * The old palette was four ad-hoc navy shades plus whatever purple-500 and
 * gray-400 each page happened to reach for, which is why no two pages matched.
 */
const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Surfaces — tonal layering, darkest to lightest
        "surface-container-lowest": "#010f1f",
        "surface-container-low": "#0d1c2d",
        "surface-container": "#122131",
        "surface-container-high": "#1c2b3c",
        "surface-container-highest": "#273647",
        surface: "#051424",
        "surface-dim": "#051424",
        "surface-bright": "#2c3a4c",
        "surface-variant": "#273647",
        background: "#051424",

        // Content on those surfaces
        "on-surface": "#d4e4fa",
        "on-surface-variant": "#cbc3d7",
        "on-background": "#d4e4fa",
        "inverse-surface": "#d4e4fa",
        "inverse-on-surface": "#233143",

        // Primary — the action colour, and branding
        primary: "#d0bcff",
        "on-primary": "#3c0091",
        "primary-container": "#a078ff",
        "on-primary-container": "#340080",
        "inverse-primary": "#6d3bd7",
        "primary-fixed": "#e9ddff",
        "primary-fixed-dim": "#d0bcff",
        "on-primary-fixed": "#23005c",
        "on-primary-fixed-variant": "#5516be",
        "surface-tint": "#d0bcff",

        // Secondary — informative highlights and progress
        secondary: "#adc6ff",
        "on-secondary": "#002e6a",
        "secondary-container": "#0566d9",
        "on-secondary-container": "#e6ecff",
        "secondary-fixed": "#d8e2ff",
        "secondary-fixed-dim": "#adc6ff",
        "on-secondary-fixed": "#001a42",
        "on-secondary-fixed-variant": "#004395",

        // Tertiary — muted supporting text
        tertiary: "#bec6e0",
        "on-tertiary": "#283044",
        "tertiary-container": "#8990a8",
        "on-tertiary-container": "#22293d",
        "tertiary-fixed": "#dae2fd",
        "tertiary-fixed-dim": "#bec6e0",
        "on-tertiary-fixed": "#131b2e",
        "on-tertiary-fixed-variant": "#3f465c",

        // Error
        error: "#ffb4ab",
        "on-error": "#690005",
        "error-container": "#93000a",
        "on-error-container": "#ffdad6",

        // Borders
        outline: "#958ea0",
        "outline-variant": "#494454",

        /**
         * Score semantics. The spec asks for semantic colours "slightly
         * desaturated to harmonize with the neon accents", so these are not
         * Tailwind's stock green-500 / yellow-500 / red-500 — which read as a
         * traffic light bolted onto a purple interface.
         *
         * The three bands are the API's: >= 75 accepted, 50-74 review,
         * < 50 rejected. One definition, so a band cannot mean one colour on
         * the results page and another on the shortlist.
         */
        score: {
          high: "#7ee0b8",
          medium: "#f5c86b",
          low: "#ff9f9a",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        // The spec's five roles. Headlines get tighter tracking and heavier
        // weight to hold against the dark background; body stays at 400 with
        // generous leading so it does not bleed on bright displays.
        "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-lg": ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-md": ["24px", { lineHeight: "32px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "label-sm": ["12px", { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "500" }],
      },
      borderRadius: {
        // 8px inputs and buttons, 16px cards, 24px modals.
        DEFAULT: "0.5rem",
        sm: "0.25rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.5rem",
        full: "9999px",
      },
      spacing: {
        gutter: "24px",
        "margin-desktop": "40px",
        "margin-mobile": "16px",
      },
      maxWidth: {
        container: "1440px",
      },
      boxShadow: {
        // Ambient glow, not physical occlusion: large radius, low alpha,
        // tinted with the primary rather than black.
        glow: "0 0 20px rgba(208, 188, 255, 0.25)",
        "glow-lg": "0 0 40px rgba(208, 188, 255, 0.15)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 240ms ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
