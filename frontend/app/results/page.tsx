import type { Metadata } from "next";
import { ResultsClient } from "./results-client";

export const metadata: Metadata = {
  title: "Results",
  description: "The full ranking from the latest run, with each score component broken out.",
};

export default function ResultsPage() {
  return <ResultsClient />;
}
