"use client";

import { useEffect, useState } from "react";
import {
  FileSearch,
  KeyRound,
  Cpu,
  Lightbulb,
  Loader2,
  Check,
  AlertCircle,
  type LucideIcon,
} from "lucide-react";
import { formatDuration } from "@/lib/scores";
import { cn } from "@/lib/utils";

export type PipelinePhase = "idle" | "running" | "done" | "error";

/**
 * The four agents, and what each one produced.
 *
 * This panel used to advance through the stages on a timer:
 * `setTimeout(1000)`, `setTimeout(1000)`, then the real request, then
 * `setTimeout(500)` — 2.5 seconds of theatre around a call that takes about
 * 700ms, with "Identified 45 technical skills and 12 soft skills" hardcoded
 * underneath regardless of what came back.
 *
 * The pipeline is one HTTP request and the server does not stream progress, so
 * there is no honest way to show stage three finishing before stage four
 * starts. What is honest: the request is either in flight or it is not, and
 * once it returns, each stage can report the real figure it produced. The
 * elapsed counter is measured, and it is replaced by the server's own timing
 * on completion.
 */
export interface PipelineFacts {
  candidateName?: string | null;
  cvFilename?: string | null;
  skillsFound?: number | null;
  jobsEvaluated?: number | null;
  processingTime?: number | null;
  explanationsGenerated?: number | null;
  scoringMode?: "hybrid" | "rule_based_only" | null;
}

const STAGES: {
  key: keyof typeof STAGE_DETAIL;
  title: string;
  icon: LucideIcon;
  waiting: string;
}[] = [
  { key: "parse", title: "Document parsing", icon: FileSearch, waiting: "Extracting raw text structure" },
  { key: "extract", title: "Keyword extraction", icon: KeyRound, waiting: "Identifying skills and entities" },
  { key: "match", title: "Scoring", icon: Cpu, waiting: "Evaluating against the job database" },
  { key: "insights", title: "Insights", icon: Lightbulb, waiting: "Compiling the final assessment" },
];

const STAGE_DETAIL = {
  parse: (facts: PipelineFacts) =>
    facts.cvFilename ? `Read ${facts.cvFilename}` : "Document read",
  extract: (facts: PipelineFacts) =>
    facts.skillsFound != null
      ? `${facts.skillsFound} skill${facts.skillsFound === 1 ? "" : "s"} recognised in the top match`
      : "Skills extracted",
  match: (facts: PipelineFacts) =>
    facts.jobsEvaluated != null
      ? `${facts.jobsEvaluated.toLocaleString()} jobs scored in ${formatDuration(facts.processingTime)}` +
        (facts.scoringMode === "rule_based_only" ? " — rules only, model not loaded" : "")
      : "Jobs scored",
  insights: (facts: PipelineFacts) =>
    facts.explanationsGenerated
      ? `${facts.explanationsGenerated} explanation${facts.explanationsGenerated === 1 ? "" : "s"} generated`
      : "Ranked without LLM explanations",
} satisfies Record<string, (facts: PipelineFacts) => string>;

export function ProcessingPipeline({
  phase,
  facts = {},
  error,
}: {
  phase: PipelinePhase;
  facts?: PipelineFacts;
  error?: string | null;
}) {
  return (
    <section className="glass-panel flex h-full flex-col rounded-lg p-8">
      <div className="mb-8 flex items-center justify-between gap-4">
        <h2 className="text-headline-md text-on-surface">Processing pipeline</h2>
        <span
          className={cn(
            "chip",
            phase === "running" && "bg-primary/20 text-primary",
            phase === "done" && "bg-score-high/10 text-score-high",
            phase === "error" && "bg-error/10 text-error",
            phase === "idle" && "bg-surface-container text-tertiary"
          )}
          aria-live="polite"
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full bg-current",
              phase === "running" && "animate-pulse"
            )}
            aria-hidden
          />
          {phase === "running" && (
            <>
              Running · <Elapsed />
            </>
          )}
          {phase === "done" && `Complete · ${formatDuration(facts.processingTime)}`}
          {phase === "error" && "Failed"}
          {phase === "idle" && "Standby"}
        </span>
      </div>

      <ol className="relative flex flex-1 flex-col justify-center gap-8">
        {/* The rail behind the step markers. */}
        <div className="absolute bottom-6 left-[19px] top-6 w-0.5 bg-white/10" aria-hidden />

        {STAGES.map(({ key, title, icon: Icon, waiting }) => (
          <li
            key={key}
            className={cn(
              "relative z-10 flex items-start gap-6 transition-opacity duration-500",
              phase === "idle" && "opacity-50"
            )}
          >
            <span
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 transition-colors",
                phase === "done" && "border-score-high/40 bg-score-high/10 text-score-high",
                phase === "running" && "border-primary/40 bg-primary/10 text-primary",
                phase === "error" && "border-error/40 bg-error/10 text-error",
                phase === "idle" && "border-white/10 bg-surface-variant text-on-surface-variant"
              )}
            >
              {phase === "running" ? (
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
              ) : phase === "done" ? (
                <Check className="h-5 w-5" aria-hidden />
              ) : phase === "error" ? (
                <AlertCircle className="h-5 w-5" aria-hidden />
              ) : (
                <Icon className="h-5 w-5" aria-hidden />
              )}
            </span>

            <div className="min-w-0">
              <h3 className="mb-1 font-semibold text-on-surface">{title}</h3>
              <p className="text-sm text-on-surface-variant">
                {phase === "done" ? STAGE_DETAIL[key](facts) : waiting}
              </p>
            </div>
          </li>
        ))}
      </ol>

      {phase === "error" && error && (
        <p className="mt-6 rounded border border-error/30 bg-error-container/20 p-4 text-sm text-on-error-container">
          {error}
        </p>
      )}
    </section>
  );
}

/**
 * Seconds since this component mounted.
 *
 * It is only rendered while the run is in flight, so mounting is the start of
 * the run and its state begins at zero without anything having to reset it.
 * Carrying the timer in the parent would mean either zeroing state from inside
 * an effect, or showing the previous run's duration for the first tick of the
 * next one.
 */
function Elapsed() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const startedAt = performance.now();
    const interval = setInterval(
      () => setSeconds((performance.now() - startedAt) / 1000),
      100
    );
    return () => clearInterval(interval);
  }, []);

  return <>{seconds.toFixed(1)}s</>;
}
