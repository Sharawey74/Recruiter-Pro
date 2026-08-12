"use client";

import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { bandStyles, scoreBand } from "@/lib/scores";
import type { MatchStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const BAND_ICON: Record<MatchStatus, typeof CheckCircle2> = {
  accepted: CheckCircle2,
  review: AlertTriangle,
  rejected: XCircle,
};

interface ScoreRingProps {
  score: number;
  /** The API's verdict. Falls back to deriving the band from the score. */
  status?: MatchStatus;
  size?: number;
  strokeWidth?: number;
  /** Shows the band icon under the number. Off on dense grids. */
  showIcon?: boolean;
  className?: string;
}

/**
 * The headline score as a ring.
 *
 * Colour alone carried the verdict before, which leaves the roughly 1 in 12
 * users with a red/green deficiency unable to tell an accepted match from a
 * rejected one. The band icon and the accessible label both say it in words.
 */
export function ScoreRing({
  score,
  status,
  size = 64,
  strokeWidth = 6,
  showIcon = true,
  className,
}: ScoreRingProps) {
  const band = status ?? scoreBand(score);
  const styles = bandStyles(score, band);
  const Icon = BAND_ICON[band];

  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  // Clamped: a score outside 0–100 would otherwise draw an inverted arc.
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div
      className={cn("relative inline-flex shrink-0 items-center justify-center", className)}
      role="img"
      aria-label={`Match score ${Math.round(score)} percent — ${styles.label}`}
    >
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          className="stroke-surface-container-highest"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={cn(styles.ring, "transition-[stroke-dashoffset] duration-700 ease-out")}
        />
      </svg>

      <span className="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span className={cn("font-bold", styles.text)} style={{ fontSize: size * 0.28 }}>
          {Math.round(score)}
        </span>
        {showIcon && size >= 56 && (
          <Icon className={cn("mt-0.5 h-3 w-3", styles.text)} aria-hidden />
        )}
      </span>
    </div>
  );
}
