import type { Metadata } from "next";
import { DashboardClient } from "./dashboard-client";

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "Upload a CV and score it against the live job corpus in a single pass.",
};

export default function DashboardPage() {
  return <DashboardClient />;
}
