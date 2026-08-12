import type { Metadata } from "next";
import { HistoryClient } from "./history-client";

export const metadata: Metadata = {
  title: "History",
  description: "Every match ever stored, with the candidate, role and score.",
};

export default function HistoryPage() {
  return <HistoryClient />;
}
