"use client";

import type { Match } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * How the rule-based total was arrived at, as one bar.
 *
 * The card already shows each component as its own meter, which answers "how
 * did the candidate do on skills". This answers a different and more useful
 * question: *which components produced this number*. A candidate at 74 because
 * their skills are excellent is a different candidate from one at 74 because
 * everything is mediocre, and four independent meters make you do that
 * arithmetic yourself.
 *
 * Each segment is the component's score multiplied by its weight, so the widths
 * are contributions to the total rather than the scores themselves — the
 * segments therefore sum to the rule-based total, and a component with a high
 * score but a 5% weight looks as small as it actually is.
 */

/** The weights from config/agents.yaml. They are validated to sum to 1.0. */
const WEIGHTS = [
  { key: "skill", label: "Skills", weight: 0.5, className: "bg-secondary" },
  { key: "experience", label: "Experience", weight: 0.2, className: "bg-tertiary" },
  { key: "title", label: "Title", weight: 0.17, className: "bg-primary" },
  { key: "education", label: "Education", weight: 0.08, className: "bg-primary-container" },
  { key: "keyword", label: "Keywords", weight: 0.05, className: "bg-score-medium" },
] as const;

export function ScoreComposition({ match }: { match: Match }) {
  const scores: Record<string, number | undefined> = {
    skill: match.skill_score,
    experience: match.experience_score,
    title: match.title_score,
    education: match.education_score,
    keyword: match.keyword_score,
  };

  // History rows predate the three new fields, so a stored match cannot be
  // decomposed. Showing a bar built from two of five components would be a
  // chart that quietly lies; showing nothing is correct.
  const complete = WEIGHTS.every(({ key }) => typeof scores[key] === "number");
  if (!complete) return null;

  const segments = WEIGHTS.map((component) => ({
    ...component,
    score: scores[component.key] as number,
    contribution: (scores[component.key] as number) * component.weight,
  }));

  const total = segments.reduce((sum, s) => sum + s.contribution, 0);

  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <span className="label-sm text-tertiary">Where the score came from</span>
        <span className="font-mono text-label-sm text-on-surface-variant">
          {total.toFixed(1)} rule-based
        </span>
      </div>

      {/*
        Widths are percentages of 100, not of the total — so a low-scoring match
        renders a short bar rather than a full one split five ways. The bar is
        the score; the segments are its parts.
      */}
      <div
        className="flex h-3 w-full overflow-hidden rounded-full bg-surface-container-highest"
        role="img"
        aria-label={segments
          .map((s) => `${s.label} contributed ${s.contribution.toFixed(1)} points`)
          .join(", ")}
      >
        {segments.map((segment) => (
          <span
            key={segment.key}
            className={cn("h-full first:rounded-l-full", segment.className)}
            style={{ width: `${segment.contribution}%` }}
            title={`${segment.label}: ${segment.score.toFixed(1)} × ${segment.weight} = ${segment.contribution.toFixed(1)} points`}
          />
        ))}
      </div>

      <ul className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1">
        {segments.map((segment) => (
          <li
            key={segment.key}
            className="flex items-center gap-1.5 text-xs text-on-surface-variant"
          >
            <span className={cn("h-2 w-2 shrink-0 rounded-sm", segment.className)} aria-hidden />
            {segment.label}
            <span className="font-mono text-tertiary">
              +{segment.contribution.toFixed(1)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
