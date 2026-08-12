import type { Metadata } from "next";
import { Suspense } from "react";
import { JobsClient } from "./jobs-client";
import { CardSkeletonGrid } from "@/components/ui/feedback";

export const metadata: Metadata = {
  title: "Jobs",
  description: "Search and filter the job corpus by title, skill, category, work model and seniority.",
};

export default function JobsPage() {
  // useSearchParams suspends during prerender; without a boundary the whole
  // route opts out of static generation and the build warns.
  return (
    <Suspense fallback={<CardSkeletonGrid count={6} />}>
      <JobsClient />
    </Suspense>
  );
}
