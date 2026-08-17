"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Star,
  WifiOff,
  Building2,
  MapPin,
  RotateCcw,
  Download,
} from "lucide-react";
import { getMatchHistory, apiErrorMessage } from "@/lib/api";
import { useSession } from "@/lib/store";
import { matchesToCsv, csvFilename, downloadCsv } from "@/lib/csv";
import type { Match, MatchStatus } from "@/lib/types";
import { bandStyles } from "@/lib/scores";
import { formatDateTime, initials, cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/page-header";
import { ScoreRing } from "@/components/ui/score-ring";
import { ScoreBarCompact } from "@/components/ui/score-bar";
import { SkillBadgeList } from "@/components/ui/skill-badge";
import { StatCard } from "@/components/ui/stat-card";
import { CardSkeletonGrid, EmptyState, ErrorState } from "@/components/ui/feedback";

/** Per candidate, only their strongest few roles are worth triaging. */
const TOP_PER_CANDIDATE = 5;
const HISTORY_LIMIT = 500;

type Filter = "all" | MatchStatus;

const TABS: { key: Filter; label: string; icon: typeof Star }[] = [
  { key: "all", label: "All", icon: Star },
  { key: "accepted", label: "Accepted", icon: CheckCircle2 },
  { key: "review", label: "Review", icon: AlertTriangle },
  { key: "rejected", label: "Rejected", icon: XCircle },
];

export function ShortlistClient() {
  const session = useSession();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  // Bumped by the retry button. Refetching by changing an input to the effect
  // keeps the fetch inside it, so nothing sets state synchronously during the
  // effect body and an unmount mid-flight cannot write to a dead component.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const response = await getMatchHistory(HISTORY_LIMIT, 0);
        if (cancelled) return;
        setError(null);
        setMatches(Array.isArray(response.matches) ? response.matches : []);
      } catch (caught) {
        if (cancelled) return;
        setError(apiErrorMessage(caught, "Failed to load candidates"));
        setMatches([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const retry = () => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  };

  /** Each candidate's strongest roles, so one CV cannot flood the board. */
  const shortlist = useMemo(() => {
    const byCandidate = new Map<string, Match[]>();
    for (const match of matches) {
      const key = match.candidate_name || match.cv_filename || "Unknown";
      const bucket = byCandidate.get(key);
      if (bucket) bucket.push(match);
      else byCandidate.set(key, [match]);
    }

    return [...byCandidate.values()].flatMap((group) =>
      [...group]
        .sort((a, b) => b.final_score - a.final_score)
        .slice(0, TOP_PER_CANDIDATE)
    );
  }, [matches]);

  const counts = useMemo(() => {
    const tally: Record<MatchStatus, number> = {
      accepted: 0,
      review: 0,
      rejected: 0,
    };
    // Only after hydration: statusOverrides live in localStorage, so counting
    // before the effect has read it renders one number on the server and a
    // different one on the client.
    if (session.hydrated) {
      for (const match of shortlist) tally[session.effectiveStatus(match)] += 1;
    }
    return tally;
  }, [shortlist, session]);

  const visible = session.hydrated
    ? shortlist.filter(
        (match) => filter === "all" || session.effectiveStatus(match) === filter
      )
    : [];

  const overrideCount = Object.keys(session.statusOverrides).length;

  const exportCsv = () => {
    if (visible.length === 0) {
      toast.error("Nothing to export.");
      return;
    }
    downloadCsv(
      csvFilename(filter === "all" ? "shortlist" : `shortlist-${filter}`),
      matchesToCsv(visible, session.effectiveStatus)
    );
    toast.success(`Exported ${visible.length} row${visible.length === 1 ? "" : "s"}.`);
  };

  return (
    <>
      <PageHeader
        title="Shortlist"
        subtitle={`Each candidate's top ${TOP_PER_CANDIDATE} roles, banded by score. Change a verdict and it sticks to this browser.`}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            {/*
              A shortlist is the thing a recruiter hands to somebody else, so
              this is the export that matters most — more than the full ranking,
              which is working material. It exports the filtered view, because
              the filter is the shortlisting.
            */}
            <button
              type="button"
              onClick={exportCsv}
              disabled={visible.length === 0}
              className="btn-secondary disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Download className="h-4 w-4" aria-hidden />
              Export {filter === "all" ? "shortlist" : filter}
            </button>

            {overrideCount > 0 && (
              <button
                type="button"
                onClick={() => {
                  session.update({ statusOverrides: {} });
                  toast.success(`Reset ${overrideCount} manual decisions.`);
                }}
                className="btn-ghost"
              >
                <RotateCcw className="h-4 w-4" aria-hidden />
                Reset {overrideCount} override{overrideCount === 1 ? "" : "s"}
              </button>
            )}
          </div>
        }
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map(({ key, label, icon: Icon }) => {
          const count = key === "all" ? shortlist.length : counts[key];
          const isActive = filter === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => setFilter(key)}
              aria-pressed={isActive}
              className={cn(
                "flex items-center gap-2 rounded px-5 py-3 font-medium transition-all",
                isActive
                  ? "bg-primary text-on-primary shadow-glow"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-bright"
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
              <span className="font-mono text-xs opacity-70">
                {session.hydrated ? count : "—"}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard
          icon={CheckCircle2}
          tone="high"
          label="Accepted"
          value={session.hydrated ? counts.accepted : "—"}
        />
        <StatCard
          icon={AlertTriangle}
          tone="medium"
          label="Needs review"
          value={session.hydrated ? counts.review : "—"}
        />
        <StatCard
          icon={XCircle}
          tone="low"
          label="Rejected"
          value={session.hydrated ? counts.rejected : "—"}
        />
      </div>

      {error && matches.length === 0 ? (
        <ErrorState
          icon={WifiOff}
          title="Could not load candidates"
          message={error}
          onRetry={retry}
        />
      ) : loading || !session.hydrated ? (
        <CardSkeletonGrid count={4} />
      ) : visible.length === 0 ? (
        <EmptyState
          icon={Star}
          title={
            shortlist.length === 0
              ? "No candidates yet"
              : `Nothing in ${filter}`
          }
          body={
            shortlist.length === 0
              ? "Analyse a résumé and its matches land here for triage."
              : "Move a candidate into this band from another tab."
          }
          action={
            shortlist.length === 0
              ? { label: "Analyse a résumé", href: "/upload" }
              : undefined
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          {visible.map((match) => (
            <CandidateCard
              key={match.match_id}
              match={match}
              status={session.effectiveStatus(match)}
              isOverridden={match.match_id in session.statusOverrides}
              onChange={(status) => {
                session.setStatus(match.match_id, status);
                toast.success(`Moved to ${status}.`);
              }}
            />
          ))}
        </div>
      )}
    </>
  );
}

function CandidateCard({
  match,
  status,
  isOverridden,
  onChange,
}: {
  match: Match;
  status: MatchStatus;
  isOverridden: boolean;
  onChange: (status: MatchStatus) => void;
}) {
  const styles = bandStyles(match.final_score, status);
  const name = match.candidate_name || match.cv_filename || "Unknown candidate";
  const location = [match.location_city, match.location_country]
    .filter(Boolean)
    .join(", ");

  return (
    <article
      className={cn("glass-panel rounded-lg border-l-4 p-6", styles.border)}
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded bg-secondary-container/40 font-mono text-sm font-semibold text-secondary">
            {initials(name)}
          </span>
          <div className="min-w-0">
            <div className="mb-1 flex items-center gap-2">
              <span className={cn("chip capitalize", styles.bg, styles.text)}>
                {status}
              </span>
              {/* Says the verdict was set by a person, not derived from the
                  score — otherwise a manual decision is indistinguishable
                  from the automatic banding. */}
              {isOverridden && (
                <span className="label-sm text-tertiary">manual</span>
              )}
            </div>
            <h3 className="truncate font-bold text-on-surface">{name}</h3>
            <p className="truncate text-sm text-on-surface-variant">
              {match.job_title}
            </p>
          </div>
        </div>

        <ScoreRing score={match.final_score} status={status} size={64} />
      </div>

      <div className="mb-4 flex flex-wrap gap-x-4 gap-y-1 text-xs text-tertiary">
        <span className="flex items-center gap-1">
          <Building2 className="h-3 w-3" aria-hidden />
          {match.company_name}
        </span>
        {location && (
          <span className="flex items-center gap-1">
            <MapPin className="h-3 w-3" aria-hidden />
            {location}
          </span>
        )}
        <span>{formatDateTime(match.timestamp)}</span>
      </div>

      <div className="mb-4 space-y-2">
        <ScoreBarCompact component="skill" value={match.skill_score} />
        <ScoreBarCompact component="experience" value={match.experience_score} />
        <ScoreBarCompact component="rules" value={match.rule_based_score} />
      </div>

      {!!match.matched_skills?.length && (
        <div className="mb-4">
          <SkillBadgeList skills={match.matched_skills} type="matched" limit={4} />
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {(["accepted", "review", "rejected"] as const)
          .filter((option) => option !== status)
          .map((option) => {
            const optionStyles = bandStyles(0, option);
            const Icon =
              option === "accepted"
                ? CheckCircle2
                : option === "review"
                  ? AlertTriangle
                  : XCircle;
            return (
              <button
                key={option}
                type="button"
                onClick={() => onChange(option)}
                className={cn(
                  "flex flex-1 items-center justify-center gap-1.5 rounded border px-3 py-2 text-xs font-medium capitalize transition-colors",
                  optionStyles.border,
                  optionStyles.bg,
                  optionStyles.text
                )}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden />
                {option}
              </button>
            );
          })}

        <Link
          href={`/jobs/${encodeURIComponent(match.job_id)}`}
          className="btn-ghost shrink-0 px-3 py-2 text-xs"
        >
          Job
        </Link>
      </div>
    </article>
  );
}
