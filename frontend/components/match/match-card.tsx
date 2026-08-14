"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2,
  MapPin,
  Briefcase,
  Wallet,
  CalendarDays,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ExternalLink,
  TrendingUp,
  FileText,
} from "lucide-react";
import type { Match } from "@/lib/types";
import { bandStyles } from "@/lib/scores";
import { ScoreRing } from "@/components/ui/score-ring";
import { ScoreBar } from "@/components/ui/score-bar";
import { SkillBadge, SkillBadgeList } from "@/components/ui/skill-badge";
import { CategoryIcon } from "@/components/jobs/job-card";
import { formatDate, cn } from "@/lib/utils";

/**
 * One CV-to-job match.
 *
 * Every figure shown here comes off the payload. The collapsed card used to
 * fall back to a hardcoded sentence about "user-centric design principles and
 * proficiency in Figma" whenever a match had no explanation, and to the literal
 * skills ["React", "TypeScript"] when it had no matched skills — so a card
 * could confidently describe a warehouse role in terms of Figma.
 */
export function MatchCard({
  match,
  defaultExpanded = false,
}: {
  match: Match;
  defaultExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const styles = bandStyles(match.final_score, match.status);
  const location = [match.location_city, match.location_country]
    .filter(Boolean)
    .join(", ");

  return (
    <article
      className={cn(
        "glass-panel rounded-lg border-l-4 p-6 transition-colors",
        styles.border
      )}
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-4">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md border border-white/5 bg-surface-container-highest">
            <CategoryIcon category={match.category} className="h-6 w-6 text-secondary" />
          </span>
          <div className="min-w-0">
            <h3 className="truncate text-lg font-bold text-on-surface">
              {match.job_title}
            </h3>
            <p className="flex items-center gap-1.5 truncate text-sm text-primary">
              <Building2 className="h-3.5 w-3.5 shrink-0" aria-hidden />
              {match.company_name || "Unknown company"}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          <ScoreRing score={match.final_score} status={match.status} size={64} />
          <span className={cn("chip", styles.bg, styles.text)}>
            <TrendingUp className="h-3 w-3" aria-hidden />
            {styles.label}
          </span>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-tertiary">
        {location && (
          <span className="flex items-center gap-1">
            <MapPin className="h-3 w-3" aria-hidden />
            {location}
          </span>
        )}
        <span className="flex items-center gap-1 capitalize">
          <Briefcase className="h-3 w-3" aria-hidden />
          {match.remote_type} · {match.seniority_level}
        </span>
        {match.salary_range && (
          <span className="flex items-center gap-1">
            <Wallet className="h-3 w-3" aria-hidden />
            {match.salary_range}
          </span>
        )}
        {match.posted_date && (
          <span className="flex items-center gap-1">
            <CalendarDays className="h-3 w-3" aria-hidden />
            Posted {formatDate(match.posted_date)}
          </span>
        )}
      </div>

      {match.explanation && (
        <p className="mb-4 line-clamp-2 text-sm text-on-surface-variant">
          {match.explanation}
        </p>
      )}

      {/* Matched first, then the gaps — the two facts a recruiter scans for. */}
      <div className="mb-4 flex flex-wrap gap-2">
        {match.matched_skills?.slice(0, 4).map((skill) => (
          <SkillBadge key={`m-${skill}`} skill={skill} type="matched" />
        ))}
        {match.missing_skills?.slice(0, 2).map((skill) => (
          <SkillBadge key={`x-${skill}`} skill={skill} type="missing" />
        ))}
        {!match.matched_skills?.length && !match.missing_skills?.length && (
          <span className="text-xs text-tertiary">
            No skill breakdown recorded for this match.
          </span>
        )}
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => setExpanded((open) => !open)}
          aria-expanded={expanded}
          className="btn-ghost flex-1"
        >
          {expanded ? "Hide breakdown" : "Score breakdown"}
          {expanded ? (
            <ChevronUp className="h-4 w-4" aria-hidden />
          ) : (
            <ChevronDown className="h-4 w-4" aria-hidden />
          )}
        </button>
        <Link
          href={`/jobs/${encodeURIComponent(match.job_id)}`}
          className="btn-ghost shrink-0"
        >
          View job
          <ExternalLink className="h-4 w-4" aria-hidden />
        </Link>
      </div>

      {expanded && (
        <div className="mt-4 animate-fade-up space-y-4 border-t border-white/10 pt-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <ScoreBar component="skill" value={match.skill_score} />
            <ScoreBar component="experience" value={match.experience_score} />
            <ScoreBar component="rules" value={match.rule_based_score} />
            <ScoreBar component="ml" value={match.ml_score} />
          </div>

          {match.explanation && (
            <section>
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-on-surface">
                <Sparkles className="h-4 w-4 text-primary" aria-hidden />
                Explanation
                <ExplanationSource source={match.explanation_source} />
              </h4>
              <p className="text-sm leading-relaxed text-on-surface-variant">
                {match.explanation}
              </p>
            </section>
          )}

          {!!match.missing_skills?.length && (
            <section className="rounded border border-score-medium/30 bg-score-medium/10 p-4">
              <h4 className="mb-2 text-sm font-semibold text-score-medium">
                Gaps against this role
              </h4>
              <SkillBadgeList
                skills={match.missing_skills}
                type="missing"
                limit={8}
              />
            </section>
          )}

          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            <Fact
              label="Experience wanted"
              value={`${match.min_experience_years}–${match.max_experience_years} yrs`}
            />
            <Fact label="Employment" value={match.employment_type} />
            <Fact label="Job ID" value={match.job_id} mono />
          </dl>
        </div>
      )}
    </article>
  );
}

function Fact({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded bg-white/5 p-3">
      <dt className="mb-1 text-xs text-tertiary">{label}</dt>
      <dd
        className={cn(
          "truncate font-semibold capitalize text-on-surface",
          mono && "font-mono text-xs normal-case"
        )}
      >
        {value}
      </dd>
    </div>
  );
}

/**
 * Which provider wrote this explanation.
 *
 * The last silent-degradation path in the product. A rule-based explanation
 * and a model-written one are both fluent, professional paragraphs, so with a
 * provider configured but unreachable — a dead key, an exhausted quota, a
 * network failure — the demo looks exactly like a working one. The scoring
 * mode already says whether the ML model ran; this says the same for the
 * prose.
 */
function ExplanationSource({ source }: { source?: string | null }) {
  if (!source) return null;

  const wasModel = source !== "rule_based";
  return (
    <span
      className={cn(
        "chip ml-auto",
        wasModel
          ? "bg-primary/10 text-primary"
          : "bg-surface-container text-tertiary"
      )}
      title={
        wasModel
          ? `Written by the ${source} provider.`
          : "Written by the rule-based fallback — no model produced this."
      }
    >
      {wasModel ? (
        <Sparkles className="h-3 w-3" aria-hidden />
      ) : (
        <FileText className="h-3 w-3" aria-hidden />
      )}
      {source.replace(/_/g, "-")}
    </span>
  );
}
