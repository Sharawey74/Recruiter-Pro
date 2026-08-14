"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Sparkles, FileSearch, ArrowRight, Play } from "lucide-react";
import { matchCV, apiErrorMessage } from "@/lib/api";
import { useSession } from "@/lib/store";
import { formatDuration } from "@/lib/scores";
import type { Match } from "@/lib/types";
import { CvDropzone } from "@/components/upload/cv-dropzone";
import {
  ProcessingPipeline,
  type PipelinePhase,
  type PipelineFacts,
} from "@/components/pipeline/processing-pipeline";
import { MatchCard } from "@/components/match/match-card";
import { CardSkeletonGrid, EmptyState } from "@/components/ui/feedback";

/** Enough to be useful on the dashboard; Results shows the full ranking. */
const DASHBOARD_TOP_K = 3;

export function DashboardClient() {
  const session = useSession();
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<PipelinePhase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [facts, setFacts] = useState<PipelineFacts>({});
  const [matches, setMatches] = useState<Match[]>([]);

  const run = async () => {
    if (!file) return;

    setPhase("running");
    setError(null);
    setMatches([]);

    try {
      const response = await matchCV(file, DASHBOARD_TOP_K, session.useLLM);
      const found = response.matches ?? [];

      setMatches(found);
      setFacts({
        cvFilename: file.name,
        candidateName: found[0]?.candidate_name ?? null,
        // The top match's coverage is the only skill figure the payload
        // supports. The old panel claimed "45 technical skills and 12 soft
        // skills" on every run, a constant string in the markup.
        skillsFound: found[0]
          ? (found[0].matched_skills?.length ?? 0)
          : null,
        jobsEvaluated: response.jobs_evaluated ?? null,
        processingTime: response.processing_time ?? null,
        explanationsGenerated: found.filter((match) => match.explanation).length,
        scoringMode: response.scoring_mode ?? null,
      });
      setPhase("done");

      // Persisted so Results and Shortlist see this run without re-uploading.
      session.record({
        matches: found,
        cvFilename: file.name,
        processingTime: response.processing_time,
        jobsEvaluated: response.jobs_evaluated,
        scoringMode: response.scoring_mode,
      });

      if (found.length === 0) {
        toast.warning("No jobs scored above zero for this CV.");
      } else {
        toast.success(
          `Scored ${response.jobs_evaluated?.toLocaleString() ?? "the corpus"} jobs in ${formatDuration(response.processing_time)}.`
        );
      }

      if (response.scoring_mode === "rule_based_only") {
        toast.warning(
          "The ML model did not load — these scores are rule-based only."
        );
      }
    } catch (caught) {
      // This page swallowed every failure into console.error and reset the
      // stepper to idle, so a dead backend looked exactly like never having
      // pressed the button.
      const message = apiErrorMessage(caught, "Matching failed");
      setError(message);
      setPhase("error");
      toast.error(message);
    }
  };

  return (
    <>
      <section className="flex flex-col items-center gap-6 py-12 text-center">
        <h1 className="text-display-lg text-balance text-on-surface">
          Optimize your hiring pipeline
        </h1>
        <p className="max-w-2xl text-lg text-on-surface-variant">
          Parse a résumé, extract its skills, and score it against every open role
          in the corpus — in one pass, with the reasoning shown.
        </p>
      </section>

      <div className="grid grid-cols-12 gap-gutter">
        <div className="col-span-12 lg:col-span-7">
          <CvDropzone
            files={file ? [file] : []}
            onFilesAdded={(accepted) => {
              setFile(accepted[0] ?? null);
              setPhase("idle");
              setError(null);
            }}
            onRemove={() => {
              setFile(null);
              setPhase("idle");
            }}
            onReject={(message) => toast.error(message)}
            disabled={phase === "running"}
          />

          {/*
            A contained row rather than a bare flex line. The label was allowed
            to size itself next to a shrink-0 button, so at some widths its
            second sentence overflowed the row and collided with the heading
            below. min-w-0 lets it wrap, and flex-wrap moves the button under
            it when there is genuinely no room.
          */}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-white/5 bg-surface-container/40 p-4">
            <label className="flex min-w-0 flex-1 cursor-pointer items-start gap-3 text-sm">
              <input
                type="checkbox"
                checked={session.useLLM}
                onChange={(event) =>
                  session.update({ useLLM: event.target.checked })
                }
                className="checkbox mt-0.5"
              />
              <span className="min-w-0">
                <span className="font-medium text-on-surface">
                  Write explanations
                </span>
                <span className="block text-tertiary">
                  Asks the configured LLM provider to justify each match. Slower,
                  and it needs a provider configured.
                </span>
              </span>
            </label>

            <button
              type="button"
              onClick={run}
              disabled={!file || phase === "running"}
              className="btn-primary shrink-0"
            >
              <Play className="h-5 w-5" aria-hidden />
              {phase === "running" ? "Analysing…" : "Analyse résumé"}
            </button>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5">
          <ProcessingPipeline phase={phase} facts={facts} error={error} />
        </div>
      </div>

      <section className="mt-16 border-t border-white/5 pt-10">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-headline-lg text-on-surface">Top matches</h2>
            {phase === "done" && (
              <p className="mt-1 text-sm text-on-surface-variant">
                Best {matches.length} of {facts.jobsEvaluated?.toLocaleString() ?? "?"}{" "}
                roles scored in {formatDuration(facts.processingTime)}.
              </p>
            )}
          </div>
          {matches.length > 0 && (
            <Link href="/results" className="btn-ghost">
              Full ranking
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          )}
        </div>

        {phase === "running" ? (
          <CardSkeletonGrid count={DASHBOARD_TOP_K} />
        ) : matches.length > 0 ? (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {matches.map((match) => (
              <MatchCard key={match.match_id} match={match} />
            ))}
          </div>
        ) : session.hydrated && session.matches.length > 0 ? (
          <EmptyState
            icon={Sparkles}
            title="Your last run is still here"
            body={`${session.matches.length} matches from ${session.cvFilename ?? "a previous CV"}. Upload another résumé above, or open the full ranking.`}
            action={{ label: "Open results", href: "/results" }}
          />
        ) : (
          <EmptyState
            icon={FileSearch}
            title="Nothing analysed yet"
            body="Drop a résumé above to score it against the job corpus. Nothing is uploaded until you press Analyse."
            action={{ label: "Browse the job corpus", href: "/jobs" }}
          />
        )}
      </section>
    </>
  );
}
