"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  ArrowLeft,
  Building2,
  MapPin,
  Briefcase,
  Wallet,
  GraduationCap,
  CalendarDays,
  Clock,
  Play,
  SearchX,
  WifiOff,
  ThumbsUp,
  AlertTriangle,
  ListChecks,
} from "lucide-react";
import { getJob, matchSingleJob, apiErrorMessage } from "@/lib/api";
import type { JobDetail, SingleMatchResponse } from "@/lib/types";
import { formatDate, cn } from "@/lib/utils";
import { bandStyles } from "@/lib/scores";
import { PageHeader } from "@/components/layout/page-header";
import { ScoreRing } from "@/components/ui/score-ring";
import { ScoreBar } from "@/components/ui/score-bar";
import { SkillBadgeList } from "@/components/ui/skill-badge";
import { CvDropzone } from "@/components/upload/cv-dropzone";
import { Skeleton, EmptyState, ErrorState } from "@/components/ui/feedback";
import { CategoryIcon } from "@/components/jobs/job-card";

/**
 * One job in full, with a direct CV-to-this-job match.
 *
 * Both halves close gaps in the product. Every job card in the reference
 * design carries a "Details →" affordance that had nowhere to go: this route
 * did not exist. And /match/single — the only endpoint returning the full
 * five-component breakdown, strengths, red flags and recommendations — had a
 * client function written for it that nothing ever called.
 */
export function JobDetailClient({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [matching, setMatching] = useState(false);
  const [result, setResult] = useState<SingleMatchResponse | null>(null);

  // Bumped by the retry button. Refetching by changing an input to the effect
  // keeps the fetch inside it, so nothing sets state synchronously during the
  // effect body and an unmount mid-flight cannot write to a dead component.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const detail = await getJob(jobId);
        if (cancelled) return;
        setError(null);
        setNotFound(false);
        setJob(detail);
      } catch (caught) {
        if (cancelled) return;
        const message = apiErrorMessage(caught, "Failed to load the job");
        if (message.includes("404") || message.toLowerCase().includes("not found")) {
          setNotFound(true);
        } else {
          setError(message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [jobId, reloadToken]);

  const retry = () => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  };

  const runMatch = async () => {
    if (!file) return;
    setMatching(true);
    setResult(null);
    try {
      const response = await matchSingleJob(file, jobId, false);
      setResult(response);
      toast.success(`Scored ${response.result.score.toFixed(1)}% against this role.`);
    } catch (caught) {
      toast.error(apiErrorMessage(caught, "Match failed"));
    } finally {
      setMatching(false);
    }
  };

  if (loading) return <DetailSkeleton />;

  if (notFound) {
    return (
      <EmptyState
        icon={SearchX}
        title="No such job"
        body={`Nothing in the corpus has the ID ${jobId}.`}
        action={{ label: "Back to jobs", href: "/jobs" }}
      />
    );
  }

  if (error || !job) {
    return (
      <ErrorState
        icon={WifiOff}
        title="Could not load this job"
        message={error ?? "The API returned no job."}
        onRetry={retry}
      />
    );
  }

  const location = [job.location_city, job.location_country].filter(Boolean).join(", ");

  return (
    <>
      <Link
        href="/jobs"
        className="mb-6 inline-flex items-center gap-2 text-sm text-tertiary transition-colors hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        All jobs
      </Link>

      <PageHeader
        title={job.title}
        meta={
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-tertiary">
            <span className="flex items-center gap-1.5">
              <Building2 className="h-4 w-4" aria-hidden />
              {job.company_name}
            </span>
            {location && (
              <span className="flex items-center gap-1.5">
                <MapPin className="h-4 w-4" aria-hidden />
                {location}
              </span>
            )}
            <span className="flex items-center gap-1.5 capitalize">
              <Briefcase className="h-4 w-4" aria-hidden />
              {job.remote_type} · {job.employment_type} · {job.seniority_level}
            </span>
            {job.posted_date && (
              <span className="flex items-center gap-1.5">
                <CalendarDays className="h-4 w-4" aria-hidden />
                Posted {formatDate(job.posted_date)}
              </span>
            )}
          </div>
        }
        actions={
          <span className="flex h-14 w-14 items-center justify-center rounded-md border border-white/5 bg-surface-container-highest">
            <CategoryIcon category={job.category} className="h-7 w-7 text-secondary" />
          </span>
        }
      />

      <div className="grid grid-cols-12 gap-gutter">
        <div className="col-span-12 space-y-6 lg:col-span-7">
          <section className="glass-panel rounded-lg p-6">
            <h2 className="mb-4 text-headline-md text-on-surface">Description</h2>
            {/* whitespace-pre-line: postings carry real newlines across four
                sections and bullet lists. Without it the whole thing collapses
                into one run-on paragraph. */}
            <p className="whitespace-pre-line leading-relaxed text-on-surface-variant">
              {job.description || "No description recorded for this role."}
            </p>
          </section>

          <section className="glass-panel rounded-lg p-6">
            <h2 className="mb-4 flex items-center gap-2 text-headline-md text-on-surface">
              <ListChecks className="h-5 w-5 text-primary" aria-hidden />
              Requirements
            </h2>
            <div className="space-y-4">
              <div>
                <p className="label-sm mb-2 text-tertiary">Required</p>
                <SkillBadgeList
                  skills={job.required_skills}
                  type="required"
                  limit={40}
                />
              </div>
              {!!job.preferred_skills?.length && (
                <div>
                  <p className="label-sm mb-2 text-tertiary">Preferred</p>
                  <SkillBadgeList
                    skills={job.preferred_skills}
                    type="preferred"
                    limit={40}
                  />
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="col-span-12 space-y-6 lg:col-span-5">
          <section className="glass-panel rounded-lg p-6">
            <h2 className="mb-4 text-headline-md text-on-surface">At a glance</h2>
            <dl className="space-y-3 text-sm">
              <Row icon={Wallet} label="Salary" value={job.salary_range || "Not disclosed"} />
              <Row
                icon={Clock}
                label="Experience"
                value={`${job.min_experience_years}–${job.max_experience_years} years`}
              />
              <Row
                icon={GraduationCap}
                label="Education"
                value={job.education_level || "Unspecified"}
              />
              <Row
                icon={Briefcase}
                label="Category"
                value={job.category ? job.category : "Uncategorised"}
              />
              <Row icon={ListChecks} label="Job ID" value={job.job_id} mono />
            </dl>
          </section>

          <section className="glass-panel rounded-lg p-6">
            <h2 className="mb-2 text-headline-md text-on-surface">
              Match a CV against this role
            </h2>
            <p className="mb-4 text-sm text-on-surface-variant">
              Scores one résumé against this job alone, with the full component
              breakdown rather than a single ranking position.
            </p>

            <CvDropzone
              files={file ? [file] : []}
              onFilesAdded={(accepted) => {
                setFile(accepted[0] ?? null);
                setResult(null);
              }}
              onRemove={() => setFile(null)}
              onReject={(message) => toast.error(message)}
              disabled={matching}
            />

            <button
              type="button"
              onClick={runMatch}
              disabled={!file || matching}
              className="btn-primary mt-4 w-full"
            >
              <Play className="h-5 w-5" aria-hidden />
              {matching ? "Scoring…" : "Score this CV"}
            </button>

            {result && <SingleMatchResult result={result} />}
          </section>
        </div>
      </div>
    </>
  );
}

function SingleMatchResult({ result }: { result: SingleMatchResponse }) {
  const styles = bandStyles(result.result.score);
  const { scores_breakdown: breakdown, skills, insights } = result;

  return (
    <div className="mt-6 animate-fade-up space-y-4 border-t border-white/10 pt-6">
      <div className="flex items-center gap-4">
        <ScoreRing score={result.result.score} size={72} />
        <div className="min-w-0">
          <p className={cn("text-lg font-bold capitalize", styles.text)}>
            {result.result.decision}
          </p>
          <p className="text-sm text-on-surface-variant">{result.result.reason}</p>
          <p className="label-sm mt-1 text-tertiary">
            Confidence {result.result.confidence.toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <ScoreBar component="skill" value={breakdown.skill_match} />
        <ScoreBar component="experience" value={breakdown.experience_match} />
        <ScoreBar component="rules" value={breakdown.rule_based_score} />
        <ScoreBar component="ml" value={breakdown.ml_score} />
      </div>

      {!!skills.matched.length && (
        <div>
          <p className="label-sm mb-2 text-tertiary">Matched</p>
          <SkillBadgeList skills={skills.matched} type="matched" limit={12} />
        </div>
      )}
      {!!skills.missing.length && (
        <div>
          <p className="label-sm mb-2 text-tertiary">Missing</p>
          <SkillBadgeList skills={skills.missing} type="missing" limit={12} />
        </div>
      )}

      <InsightList
        icon={ThumbsUp}
        tone="text-score-high"
        title="Strengths"
        items={insights.strengths}
      />
      <InsightList
        icon={AlertTriangle}
        tone="text-score-medium"
        title="Red flags"
        items={insights.red_flags}
      />
      <InsightList
        icon={ListChecks}
        tone="text-secondary"
        title="Recommendations"
        items={insights.recommendations}
      />
    </div>
  );
}

function InsightList({
  icon: Icon,
  tone,
  title,
  items,
}: {
  icon: typeof ThumbsUp;
  tone: string;
  title: string;
  items: string[];
}) {
  if (!items?.length) return null;
  return (
    <section>
      <h3 className={cn("mb-2 flex items-center gap-1.5 text-sm font-semibold", tone)}>
        <Icon className="h-4 w-4" aria-hidden />
        {title}
      </h3>
      <ul className="space-y-1 text-sm text-on-surface-variant">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span aria-hidden>·</span>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Row({
  icon: Icon,
  label,
  value,
  mono = false,
}: {
  icon: typeof Wallet;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="flex items-center gap-2 text-tertiary">
        <Icon className="h-4 w-4 shrink-0" aria-hidden />
        {label}
      </dt>
      <dd
        className={cn(
          "truncate text-right font-medium capitalize text-on-surface",
          mono && "font-mono text-xs normal-case"
        )}
      >
        {value}
      </dd>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading job">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-12 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
      <div className="grid grid-cols-12 gap-gutter">
        <div className="col-span-12 space-y-6 lg:col-span-7">
          <Skeleton className="h-64 w-full rounded-lg" />
          <Skeleton className="h-40 w-full rounded-lg" />
        </div>
        <div className="col-span-12 space-y-6 lg:col-span-5">
          <Skeleton className="h-52 w-full rounded-lg" />
          <Skeleton className="h-80 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}
