import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

/**
 * ESLint has never run in this repository.
 *
 * The lint script was `next lint`, which prompted interactively for a config
 * that was never committed — and which Next 16 removed outright, so the script
 * failed with "Invalid project directory provided, no such directory:
 * .../frontend/lint" (it parsed "lint" as a path argument). CI ran it under
 * continue-on-error, so the failure was invisible.
 *
 * eslint-config-next 16 exports flat config arrays directly. Going through
 * @eslint/eslintrc's FlatCompat instead throws "Converting circular structure
 * to JSON" while validating the legacy schema.
 */
const config = [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "next-env.d.ts",
      // Design references, not application source: third-party HTML with
      // inline scripts and CDN tags.
      "Images/**",
    ],
  },
  ...coreWebVitals,
  ...typescript,
  {
    rules: {
      // `any` is how the score fields went unchecked for months: every page
      // held `useState<any[]>` for its matches, so renaming a field on the
      // wire changed nothing at compile time and produced NaN at runtime.
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
];

export default config;
