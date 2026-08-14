import type { Metadata } from "next";
import { LandingClient } from "./landing-client";

export const metadata: Metadata = {
  // The root's default title, without the "· Recruiter Pro" suffix the
  // template adds — the landing page is the product, not a section of it.
  title: {
    absolute: "Recruiter Pro — CV intelligence",
  },
  description:
    "Parse a résumé, extract its skills against a curated taxonomy, and score it against every open role in one pass.",
};

export default function HomePage() {
  return <LandingClient />;
}
