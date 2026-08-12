import type { Metadata } from "next";
import { ShortlistClient } from "./shortlist-client";

export const metadata: Metadata = {
  title: "Shortlist",
  description: "Triage candidates into accepted, review and rejected.",
};

export default function ShortlistPage() {
  return <ShortlistClient />;
}
