"use client";

import { Check, X, Asterisk, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

type SkillType = "matched" | "missing" | "required" | "preferred";

/**
 * A skill, with its relationship to the job stated by an icon as well as a
 * colour. "Matched" and "missing" are opposite verdicts that differed only by
 * hue before, which is unreadable to anyone with a colour deficiency and
 * ambiguous to everyone else on a dark background.
 */
const STYLES: Record<
  SkillType,
  { className: string; icon: typeof Check; title: string }
> = {
  matched: {
    className: "border-score-high/30 bg-score-high/10 text-score-high",
    icon: Check,
    title: "Present in the CV",
  },
  missing: {
    className: "border-score-medium/30 bg-score-medium/10 text-score-medium",
    icon: X,
    title: "Required by the job, not found in the CV",
  },
  required: {
    className: "border-secondary/30 bg-secondary/10 text-secondary",
    icon: Asterisk,
    title: "Required by the job",
  },
  preferred: {
    className: "border-outline-variant/50 bg-surface-variant/50 text-on-surface-variant",
    icon: Plus,
    title: "Nice to have",
  },
};

export function SkillBadge({
  skill,
  type = "matched",
}: {
  skill: string;
  type?: SkillType;
}) {
  const { className, icon: Icon, title } = STYLES[type];

  return (
    <span
      title={`${skill} — ${title}`}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium",
        className
      )}
    >
      <Icon className="h-3 w-3 shrink-0" aria-hidden />
      {skill}
    </span>
  );
}

/**
 * A capped list of skills with a "+N more" tail, so a job with thirty
 * requirements does not push everything else off the card.
 */
export function SkillBadgeList({
  skills,
  type = "matched",
  limit = 6,
}: {
  skills?: string[] | null;
  type?: SkillType;
  limit?: number;
}) {
  if (!skills || skills.length === 0) return null;
  const shown = skills.slice(0, limit);
  const rest = skills.length - shown.length;

  return (
    <div className="flex flex-wrap gap-2">
      {shown.map((skill) => (
        <SkillBadge key={skill} skill={skill} type={type} />
      ))}
      {rest > 0 && (
        <span
          className="inline-flex items-center rounded-full border border-outline-variant/50 px-2.5 py-1 text-xs text-tertiary"
          title={skills.slice(limit).join(", ")}
        >
          +{rest} more
        </span>
      )}
    </div>
  );
}
