"use client";

import { Puzzle, Clock, ListChecks, Brain, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * One component score as a labelled meter.
 *
 * The four components are fixed, and so are their icons — the point of an icon
 * here is that a reader recognises "skills" without reading the label, which
 * only works if it means the same thing on every card.
 *
 * The labels are the ones the API now uses. They previously said "Quality",
 * "ATS" and "Matching", none of which named the number underneath: those were
 * the rule-based total, required-skill coverage and years-of-experience fit.
 */
export const SCORE_COMPONENTS = {
  skill: {
    label: "Skill coverage",
    icon: Puzzle,
    accent: "bg-secondary",
    hint: "Share of the job's required skills found in the CV.",
  },
  experience: {
    label: "Experience fit",
    icon: Clock,
    accent: "bg-tertiary",
    hint: "How the candidate's years line up with the role's range.",
  },
  rules: {
    label: "Rule-based total",
    icon: ListChecks,
    accent: "bg-primary",
    hint: "Skills, title, experience, education and keywords, weighted.",
  },
  ml: {
    label: "Model score",
    icon: Brain,
    accent: "bg-primary-container",
    hint: "The trained classifier's prediction. Absent when the model did not load.",
  },
} as const satisfies Record<
  string,
  { label: string; icon: LucideIcon; accent: string; hint: string }
>;

export type ScoreComponent = keyof typeof SCORE_COMPONENTS;

export function ScoreBar({
  component,
  value,
  className,
}: {
  component: ScoreComponent;
  /** 0–100, or null when the score did not run. */
  value: number | null | undefined;
  className?: string;
}) {
  const { label, icon: Icon, accent, hint } = SCORE_COMPONENTS[component];
  const missing = value == null;
  const clamped = Math.max(0, Math.min(100, value ?? 0));

  return (
    <div
      className={cn(
        "rounded border border-white/5 bg-surface-container/50 p-4",
        className
      )}
      title={hint}
    >
      <p className="label-sm mb-2 flex items-center gap-1.5 text-tertiary">
        <Icon className="h-3.5 w-3.5" aria-hidden />
        {label}
      </p>
      <div className="flex items-end gap-3">
        <span className="text-2xl font-bold text-on-surface">
          {missing ? "—" : `${Math.round(clamped)}%`}
        </span>
        <div className="mb-1.5 h-1.5 w-full overflow-hidden rounded-full bg-surface-container-highest">
          <div
            className={cn("h-full rounded-full transition-[width] duration-700", accent)}
            style={{ width: missing ? "0%" : `${clamped}%` }}
          />
        </div>
      </div>
    </div>
  );
}

/** The same meter at row scale, for side panels and lists. */
export function ScoreBarCompact({
  component,
  value,
}: {
  component: ScoreComponent;
  value: number | null | undefined;
}) {
  const { label, icon: Icon, accent, hint } = SCORE_COMPONENTS[component];
  const clamped = Math.max(0, Math.min(100, value ?? 0));

  return (
    <div title={hint}>
      <div className="mb-1 flex justify-between text-xs text-tertiary">
        <span className="flex items-center gap-1.5">
          <Icon className="h-3 w-3" aria-hidden />
          {label}
        </span>
        <span>{value == null ? "—" : `${Math.round(clamped)}%`}</span>
      </div>
      <div className="h-1 w-full overflow-hidden rounded-full bg-surface-container-highest">
        <div
          className={cn("h-full rounded-full transition-[width] duration-700", accent)}
          style={{ width: value == null ? "0%" : `${clamped}%` }}
        />
      </div>
    </div>
  );
}
