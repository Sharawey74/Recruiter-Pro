"use client";

import { CheckCircle2, AlertTriangle, XCircle, Gauge } from "lucide-react";
import type { Match } from "@/lib/types";
import { StatCard } from "@/components/ui/stat-card";
import { scoreBand, SCORE_THRESHOLDS } from "@/lib/scores";

/**
 * The three bands and the mean, over whichever matches are in view.
 *
 * The thresholds in the labels are read from the same constants the bands are
 * derived from, so a change to one cannot leave the other saying 75%.
 */
export function MatchSummary({ matches }: { matches: Match[] }) {
  const counts = { accepted: 0, review: 0, rejected: 0 };
  for (const match of matches) {
    counts[match.status ?? scoreBand(match.final_score)] += 1;
  }

  const average = matches.length
    ? matches.reduce((total, match) => total + match.final_score, 0) / matches.length
    : 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        icon={CheckCircle2}
        tone="high"
        label={`Strong (≥ ${SCORE_THRESHOLDS.accepted}%)`}
        value={counts.accepted}
        hint="Matches the API flagged as accepted."
      />
      <StatCard
        icon={AlertTriangle}
        tone="medium"
        label={`Worth a look (${SCORE_THRESHOLDS.review}–${SCORE_THRESHOLDS.accepted - 1}%)`}
        value={counts.review}
        hint="Matches needing a human decision."
      />
      <StatCard
        icon={XCircle}
        tone="low"
        label={`Below threshold (< ${SCORE_THRESHOLDS.review}%)`}
        value={counts.rejected}
        hint="Matches the API flagged as rejected."
      />
      <StatCard
        icon={Gauge}
        label="Average score"
        value={`${average.toFixed(1)}%`}
        hint="Mean hybrid score across the matches in view."
      />
    </div>
  );
}
