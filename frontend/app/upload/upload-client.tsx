"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Play, ArrowRight, FileText, AlertCircle } from "lucide-react";
import { matchCV, apiErrorMessage } from "@/lib/api";
import { useSession } from "@/lib/store";
import { formatDuration } from "@/lib/scores";
import type { Match } from "@/lib/types";
import { PageHeader } from "@/components/layout/page-header";
import { CvDropzone } from "@/components/upload/cv-dropzone";
import { MatchCard } from "@/components/match/match-card";
import { MatchSummary } from "@/components/match/match-summary";
import { CardSkeletonGrid } from "@/components/ui/feedback";

const TOP_K = 10;

interface CvRun {
  filename: string;
  matches: Match[];
  processingTime: number | null;
  jobsEvaluated: number | null;
  /** Whether this run used the ML model or fell back to rules. */
  scoringMode: "hybrid" | "rule_based_only" | null;
  /** Set when this CV failed; the others in the batch still ran. */
  error?: string;
}

export function UploadClient() {
  const session = useSession();
  const [files, setFiles] = useState<File[]>([]);
  const [runs, setRuns] = useState<CvRun[]>([]);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(
    null
  );

  const run = async () => {
    if (files.length === 0) {
      toast.error("Add at least one résumé first.");
      return;
    }

    setBusy(true);
    setRuns([]);
    setProgress({ done: 0, total: files.length });

    const completed: CvRun[] = [];

    for (const [index, file] of files.entries()) {
      try {
        const response = await matchCV(file, TOP_K, session.useLLM);
        completed.push({
          filename: file.name,
          matches: response.matches ?? [],
          processingTime: response.processing_time ?? null,
          jobsEvaluated: response.jobs_evaluated ?? null,
          scoringMode: response.scoring_mode ?? null,
        });
      } catch (caught) {
        // One bad file must not cost the rest of the batch. The old loop let
        // the first failure throw out of the for-loop, discarding every result
        // already collected and reporting only the last error.
        const message = apiErrorMessage(caught, `Failed to process ${file.name}`);
        completed.push({
          filename: file.name,
          matches: [],
          processingTime: null,
          jobsEvaluated: null,
          scoringMode: null,
          error: message,
        });
        toast.error(`${file.name}: ${message}`);
      }

      setProgress({ done: index + 1, total: files.length });
      setRuns([...completed]);
    }

    setBusy(false);
    setProgress(null);

    const succeeded = completed.filter((entry) => !entry.error);
    if (succeeded.length > 0) {
      // The last successful run becomes the session's current analysis, which
      // is what Results and Shortlist read.
      const latest = succeeded[succeeded.length - 1]!;
      session.record({
        matches: latest.matches,
        cvFilename: latest.filename,
        processingTime: latest.processingTime,
        jobsEvaluated: latest.jobsEvaluated,
        scoringMode: latest.scoringMode,
      });
      setFiles([]);
      toast.success(
        `Processed ${succeeded.length} of ${completed.length} résumé${completed.length === 1 ? "" : "s"}.`
      );
    }
  };

  return (
    <>
      <PageHeader
        title="Upload & match"
        subtitle="Score résumés against every open role. Each file is parsed, its skills extracted, and every job in the corpus ranked against it."
        actions={
          runs.length > 0 ? (
            <Link href="/results" className="btn-ghost">
              Open results
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          ) : undefined
        }
      />

      <div className="glass-panel rounded-lg p-8">
        <CvDropzone
          files={files}
          multiple
          onFilesAdded={(accepted) => setFiles((prev) => [...prev, ...accepted])}
          onRemove={(index) =>
            setFiles((prev) => prev.filter((_, i) => i !== index))
          }
          onReject={(message) => toast.error(message)}
          disabled={busy}
        />

        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-white/5 bg-surface-container/40 p-4">
          <label className="flex min-w-0 flex-1 cursor-pointer items-start gap-3 text-sm">
            <input
              type="checkbox"
              checked={session.useLLM}
              onChange={(event) => session.update({ useLLM: event.target.checked })}
              className="checkbox mt-0.5"
              disabled={busy}
            />
            <span className="min-w-0">
              <span className="font-medium text-on-surface">Write explanations</span>
              <span className="block text-tertiary">
                One LLM call per match. Adds roughly 30–60s per résumé and needs a
                provider configured.
              </span>
            </span>
          </label>

          <button
            type="button"
            onClick={run}
            disabled={busy || files.length === 0}
            className="btn-primary shrink-0"
          >
            <Play className="h-5 w-5" aria-hidden />
            {progress
              ? `Processing ${progress.done + 1} of ${progress.total}…`
              : `Match ${files.length || ""} résumé${files.length === 1 ? "" : "s"}`.trim()}
          </button>
        </div>
      </div>

      {busy && runs.length === 0 && (
        <div className="mt-12">
          <CardSkeletonGrid count={3} />
        </div>
      )}

      {runs.map((entry) => (
        <section key={entry.filename} className="mt-12">
          <h2 className="mb-4 flex items-center gap-2 text-headline-md text-on-surface">
            <FileText className="h-5 w-5 text-primary" aria-hidden />
            {entry.filename}
          </h2>

          {entry.error ? (
            <div
              className="flex items-start gap-3 rounded-lg border border-error/30 bg-error-container/20 p-6"
              role="alert"
            >
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-error" aria-hidden />
              <p className="text-on-surface-variant">{entry.error}</p>
            </div>
          ) : (
            <>
              <p className="mb-4 text-sm text-on-surface-variant">
                {entry.jobsEvaluated?.toLocaleString() ?? "The corpus"} roles scored in{" "}
                {formatDuration(entry.processingTime)} · showing the top{" "}
                {entry.matches.length}.
              </p>

              <MatchSummary matches={entry.matches} />

              <div className="mt-6 space-y-4">
                {entry.matches.map((match) => (
                  <MatchCard key={match.match_id} match={match} />
                ))}
              </div>
            </>
          )}
        </section>
      ))}
    </>
  );
}
