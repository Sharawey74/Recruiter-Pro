import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/app-shell";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  // `%s` is filled by each route's own metadata. Every page shared the single
  // title "AI Resume Matcher - Dashboard" before, so six open tabs were
  // indistinguishable and the browser history recorded one page.
  title: {
    default: "Recruiter Pro",
    template: "%s · Recruiter Pro",
  },
  description:
    "CV screening against a live job corpus: parse, extract, score and explain, with a four-agent pipeline.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <head>
        {/*
          Inter and JetBrains Mono, the two families the design system
          specifies. Loaded with a plain <link> rather than next/font because
          next/font fetches at build time and fails the build outright without
          a network; a <link> degrades to the system stack instead.
        */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font --
            The rule targets per-page font links in the pages router, where
            they load for one route only. This is the root layout of the app
            router, so it applies to every page — which is exactly the rule's
            requirement. */}
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {/* The frame is a client component because the navigation drawer needs
            open/closed state below lg. `children` is passed through as a prop,
            so the pages themselves stay server components. */}
        <AppShell>{children}</AppShell>
        <Toaster position="top-right" theme="dark" richColors closeButton />
      </body>
    </html>
  );
}
