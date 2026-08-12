import type { MatchStatus } from "./types";

/**
 * The score bands, in one place.
 *
 * These thresholds live in src/api.py, which stamps every match with a status.
 * Six components re-derived them from `final_score` with their own inline
 * `>= 75 ? green : >= 50 ? yellow : red`, and they had already diverged: the
 * match card used orange below 50 where every other surface used red, so the
 * same score looked like a different verdict depending on where you saw it.
 */
export const SCORE_THRESHOLDS = { accepted: 75, review: 50 } as const;

export function scoreBand(score: number): MatchStatus {
  if (score >= SCORE_THRESHOLDS.accepted) return "accepted";
  if (score >= SCORE_THRESHOLDS.review) return "review";
  return "rejected";
}

/** Tailwind classes per band. `band` is the API's status when one is present. */
export const BAND_STYLES: Record<
  MatchStatus,
  { text: string; bg: string; border: string; ring: string; hex: string; label: string }
> = {
  accepted: {
    text: "text-score-high",
    bg: "bg-score-high/10",
    border: "border-score-high/40",
    ring: "stroke-score-high",
    hex: "#7ee0b8",
    label: "Strong match",
  },
  review: {
    text: "text-score-medium",
    bg: "bg-score-medium/10",
    border: "border-score-medium/40",
    ring: "stroke-score-medium",
    hex: "#f5c86b",
    label: "Worth a look",
  },
  rejected: {
    text: "text-score-low",
    bg: "bg-score-low/10",
    border: "border-score-low/40",
    ring: "stroke-score-low",
    hex: "#ff9f9a",
    label: "Below threshold",
  },
};

export function bandStyles(score: number, status?: MatchStatus) {
  return BAND_STYLES[status ?? scoreBand(score)];
}

export function formatScore(score: number): string {
  return `${Math.round(score)}%`;
}

/**
 * Seconds, as the results header reports them. Sub-second durations are the
 * normal case since matching was batched, and "0s" reads as "nothing ran".
 */
export function formatDuration(seconds?: number | null): string {
  if (seconds == null) return "—";
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  return `${seconds.toFixed(2)}s`;
}
