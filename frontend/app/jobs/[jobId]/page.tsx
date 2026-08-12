import type { Metadata } from "next";
import { JobDetailClient } from "./job-detail-client";

export const metadata: Metadata = {
  title: "Job detail",
  description: "The full posting, its requirements, and a direct match against one CV.",
};

export default async function JobDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return <JobDetailClient jobId={decodeURIComponent(jobId)} />;
}
