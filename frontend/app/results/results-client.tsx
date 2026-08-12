"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Download, CheckCircle2, FileSearch, Cpu, Clock } from "lucide-react";
import { useSession } from "@/lib/store";
import { formatDuration, SCORE_THRESHOLDS } from "@/lib/scores";
import { formatDateTime } from "@/lib/utils";
import { PageHeader } from "@/components/layout/page-header";
import { MatchCard } from "@/components/match/match-card";
import { MatchSummary } from "@/components/match/match-summary";
import { CardSkeletonGrid, EmptyState } from "@/components/ui/feedback";
import type { Match } from "@/lib/types";

type SortKey = "score" | "company" | "title";

/**
 * The latest run's full ranking.
 *
 * This page used to load /match/history, which meant it showed every match
 * ever stored rather than the run the user had just performed — the header
 * said "Match Results" and the body was the entire database. The run itself
 * lives in the session store now; History remains the place to see everything.
 */
export function ResultsClient() {
  const session = useSession();
  const [minScore, setMinScore] = useState(0);
  const [sortBy, setSortBy] = useState<SortKey>("score");

  const visible = useMemo(() => {
    const filtered = session.matches.filter((match) => match.final_score >= minScore);
    const sorted = [...filtered];

    sorted.sort((a, b) => {
      if (sortBy === "score") return b.final_score - a.final_score;
      if (sortBy === "company")
        return (a.company_name ?? "").localeCompare(b.company_name ?? "");
      return (a.job_title ?? "").localeCompare(b.job_title ?? "");
    });

    return sorted;
  }, [session.matches, minScore, sortBy]);

  const exportCsv = () => {
    if (visible.length === 0) {
      toast.error("Nothing to export.");
      return;
    }
    downloadCsv(visible, session.cvFilename ?? "results");
    toast.success(`Exported ${visible.length} rows.`);
  };

  if (!session.hydrated) {
    return (
      <>
        <PageHeader title="Match results" />
        <CardSkeletonGrid count={3} />
      </>
    );
  }

  if (session.matches.length === 0) {
    return (
      <>
        <PageHeader title="Match results" />
        <EmptyState
          icon={FileSearch}
          title="No run in this session"
          body="Results show the ranking from the résumé you last analysed. Upload one to populate this page, or open History for everything scored previously."
          action={{ label: "Upload a résumé", href: "/upload" }}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Match results"
        subtitle={session.cvFilename ? `Ranking for ${session.cvFilename}` : undefined}
        meta={
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-tertiary">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-secondary" aria-hidden />
              Matched against{" "}
              <strong className="text-on-surface">
                {session.jobsEvaluated?.toLocaleString() ?? "the corpus"}
              </strong>{" "}
              jobs
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="h-4 w-4" aria-hidden />
              <strong className="text-primary">
                {formatDuration(session.processingTime)}
              </strong>
            </span>
            {/* Provenance, not decoration: a rules-only run and a hybrid run
                produce equally plausible numbers. */}
            <span className="flex items-center gap-1.5">
              <Cpu className="h-4 w-4" aria-hidden />
              {session.scoringMode === "rule_based_only"
                ? "Rule-based only — model not loaded"
                : session.scoringMode === "hybrid"
                  ? "Hybrid ML + rules"
                  : "Scoring mode unrecorded"}
            </span>
            {session.analyzedAt && <span>{formatDateTime(session.analyzedAt)}</span>}
          </div>
        }
        actions={
          <button type="button" onClick={exportCsv} className="btn-secondary">
            <Download className="h-4 w-4" aria-hidden />
            Export CSV
          </button>
        }
      />

      <MatchSummary matches={visible} />

      <div className="glass-panel my-8 flex flex-wrap items-center gap-4 rounded-lg p-4">
        <label className="flex items-center gap-2 text-sm">
          <span className="text-tertiary">Minimum score</span>
          <select
            value={minScore}
            onChange={(event) => setMinScore(Number(event.target.value))}
            className="field w-auto py-2"
          >
            <option value={0}>Any</option>
            <option value={SCORE_THRESHOLDS.review}>
              {SCORE_THRESHOLDS.review}% and up
            </option>
            <option value={SCORE_THRESHOLDS.accepted}>
              {SCORE_THRESHOLDS.accepted}% and up
            </option>
          </select>
        </label>

        <label className="flex items-center gap-2 text-sm">
          <span className="text-tertiary">Sort by</span>
          <select
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value as SortKey)}
            className="field w-auto py-2"
          >
            <option value="score">Score</option>
            <option value="company">Company</option>
            <option value="title">Job title</option>
          </select>
        </label>

        <span className="ml-auto label-sm text-tertiary">
          {visible.length} of {session.matches.length} shown
        </span>
      </div>

      {visible.length === 0 ? (
        <EmptyState
          icon={FileSearch}
          title="Nothing above that threshold"
          body={`No match in this run scored ${minScore}% or higher. Lower the minimum to see the rest.`}
        />
      ) : (
        <div className="space-y-4">
          {visible.map((match, index) => (
            <MatchCard
              key={match.match_id}
              match={match}
              // The top match opens expanded: it is the one a recruiter reads.
              defaultExpanded={index === 0}
            />
          ))}
        </div>
      )}
    </>
  );
}

/**
 * CSV, built in the browser from the rows on screen.
 *
 * The Export button existed on three pages and was wired to nothing on all
 * three. Quoting is not optional here — job titles and companies contain
 * commas, and an unquoted title shifts every later column in the row.
 */
function downloadCsv(matches: Match[], source: string) {
  const columns: [string, (match: Match) => string | number][] = [
    ["job_id", (m) => m.job_id],
    ["job_title", (m) => m.job_title],
    ["company", (m) => m.company_name ?? ""],
    ["location", (m) => [m.location_city, m.location_country].filter(Boolean).join(", ")],
    ["remote_type", (m) => m.remote_type],
    ["seniority", (m) => m.seniority_level],
    ["salary_range", (m) => m.salary_range ?? ""],
    ["final_score", (m) => m.final_score],
    ["rule_based_score", (m) => m.rule_based_score],
    ["skill_score", (m) => m.skill_score],
    ["experience_score", (m) => m.experience_score],
    ["ml_score", (m) => m.ml_score ?? ""],
    ["status", (m) => m.status],
    ["matched_skills", (m) => (m.matched_skills ?? []).join("; ")],
    ["missing_skills", (m) => (m.missing_skills ?? []).join("; ")],
  ];

  const escape = (value: string | number) =>
    `"${String(value).replace(/"/g, '""')}"`;

  const csv = [
    columns.map(([header]) => header).join(","),
    ...matches.map((match) =>
      columns.map(([, read]) => escape(read(match))).join(",")
    ),
  ].join("\r\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `recruiter-pro-${source.replace(/\.[^.]+$/, "")}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
