"use client";

import Link from "next/link";
import {
  Cpu,
  TrendingUp,
  Megaphone,
  Calculator,
  Users,
  ClipboardList,
  Wrench,
  Factory,
  Briefcase,
  MapPin,
  Building2,
  Wallet,
  ArrowRight,
  type LucideIcon,
} from "lucide-react";
import type { Job } from "@/lib/types";
import { SkillBadgeList } from "@/components/ui/skill-badge";
import { cn } from "@/lib/utils";

/**
 * One icon per business category, drawn from the corpus's own eight values.
 *
 * The reference design gives every job card a glyph tile. A single generic
 * briefcase on all eight hundred would be decoration; keyed to the category it
 * carries information, and it is the fastest way to scan a mixed grid.
 */
export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  engineering: Cpu,
  sales: TrendingUp,
  marketing: Megaphone,
  accounting: Calculator,
  management: Users,
  administrators: ClipboardList,
  maintenance: Wrench,
  operations: Factory,
};

/**
 * Rendered as a component rather than resolved to a local `const Icon` inside
 * another component's body. The lookup returns a stable reference either way,
 * but a capitalised local bound to a function is indistinguishable from a
 * component defined during render, which remounts the subtree on every render
 * when it genuinely is one.
 */
export function CategoryIcon({
  category,
  className,
}: {
  category?: string | null;
  className?: string;
}) {
  const Glyph: LucideIcon =
    CATEGORY_ICONS[(category ?? "").toLowerCase()] ?? Briefcase;
  return <Glyph className={className} aria-hidden />;
}

/** Remote arrangement, coloured so it reads at a glance across the grid. */
const REMOTE_STYLES: Record<string, string> = {
  remote: "bg-score-high/10 text-score-high",
  hybrid: "bg-secondary/10 text-secondary",
  "on-site": "bg-surface-variant/60 text-on-surface-variant",
};

export function JobCard({ job }: { job: Job }) {
  const title = job.title || "Untitled role";
  const location = [job.location_city, job.location_country]
    .filter(Boolean)
    .join(", ");

  return (
    <article className="gradient-border-card card-interactive flex flex-col justify-between border border-transparent p-6">
      <div>
        <div className="mb-4 flex items-start justify-between gap-3">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md border border-white/5 bg-surface-container-highest">
            <CategoryIcon category={job.category} className="h-6 w-6 text-secondary" />
          </span>

          <span
            className={cn(
              "chip capitalize",
              REMOTE_STYLES[job.remote_type] ?? REMOTE_STYLES["on-site"]
            )}
          >
            {job.remote_type}
          </span>
        </div>

        <h3 className="mb-1 text-xl font-semibold leading-tight text-on-surface">
          {title}
        </h3>

        <div className="mb-4 space-y-1 text-sm text-tertiary">
          <p className="flex items-center gap-1.5">
            <Building2 className="h-3.5 w-3.5 shrink-0" aria-hidden />
            <span className="truncate">{job.company_name}</span>
          </p>
          {location && (
            <p className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 shrink-0" aria-hidden />
              <span className="truncate">{location}</span>
            </p>
          )}
          <p className="flex items-center gap-1.5 capitalize">
            <Briefcase className="h-3.5 w-3.5 shrink-0" aria-hidden />
            {job.seniority_level} · {job.employment_type}
          </p>
        </div>

        <SkillBadgeList skills={job.required_skills} type="required" limit={3} />
      </div>

      <div className="mt-6 flex items-center justify-between gap-3 border-t border-white/10 pt-4">
        <span className="flex min-w-0 items-center gap-1.5 text-sm font-semibold text-secondary">
          <Wallet className="h-4 w-4 shrink-0" aria-hidden />
          <span className="truncate">{job.salary_range || "Not disclosed"}</span>
        </span>

        <Link
          href={`/jobs/${encodeURIComponent(job.job_id)}`}
          className="flex shrink-0 items-center gap-1 text-sm font-medium text-primary transition-colors hover:text-primary-fixed"
        >
          Details
          <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </div>
    </article>
  );
}
