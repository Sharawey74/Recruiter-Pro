"use client";

import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * A single headline number. Four pages had their own copy of this markup with
 * four slightly different paddings and border treatments.
 */
export function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = "neutral",
  className,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  /** Shown on hover; use it to say what the number counts. */
  hint?: string;
  tone?: "neutral" | "high" | "medium" | "low";
  className?: string;
}) {
  const tones = {
    neutral: "bg-primary/10 text-primary",
    high: "bg-score-high/10 text-score-high",
    medium: "bg-score-medium/10 text-score-medium",
    low: "bg-score-low/10 text-score-low",
  } as const;

  return (
    <div
      className={cn("glass-panel rounded-lg p-6", className)}
      title={hint}
    >
      <div className="flex items-center gap-4">
        <div className={cn("rounded-md p-3", tones[tone])}>
          <Icon className="h-6 w-6" aria-hidden />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm text-on-surface-variant">{label}</p>
          <p className="text-3xl font-bold text-on-surface">{value}</p>
        </div>
      </div>
    </div>
  );
}
