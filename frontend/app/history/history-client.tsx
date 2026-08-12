"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  Trash2,
  Users,
  Gauge,
  Layers,
  History as HistoryIcon,
  WifiOff,
  Loader2,
  Search,
} from "lucide-react";
import { getMatchHistory, clearMatchHistory, apiErrorMessage } from "@/lib/api";
import { useSession } from "@/lib/store";
import type { Match } from "@/lib/types";
import { bandStyles } from "@/lib/scores";
import { formatDateTime, initials, cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { EmptyState, ErrorState, RowSkeleton } from "@/components/ui/feedback";

const PAGE_SIZE = 20;

export function HistoryClient() {
  const session = useSession();
  const [matches, setMatches] = useState<Match[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [query, setQuery] = useState("");

  // Bumped by the retry button. Refetching by changing an input to the effect
  // keeps the fetch inside it, so nothing sets state synchronously during the
  // effect body and an unmount mid-flight cannot write to a dead component.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const response = await getMatchHistory(PAGE_SIZE, page * PAGE_SIZE);
        if (cancelled) return;
        setError(null);
        setTotal(response.total);
        setMatches((prev) =>
          page === 0 ? response.matches : [...prev, ...response.matches]
        );
      } catch (caught) {
        if (cancelled) return;
        setError(apiErrorMessage(caught, "Failed to load history"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [page, reloadToken]);

  const retry = () => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  };

  const clear = async () => {
    if (
      !window.confirm(
        `Delete all ${total} stored matches? This cannot be undone.`
      )
    ) {
      return;
    }

    setClearing(true);
    try {
      const result = await clearMatchHistory();
      setMatches([]);
      setTotal(0);
      setPage(0);
      // One call, because there is one key. Clearing used to mean remembering
      // to remove five separate localStorage entries by hand, and any page
      // that forgot one left a stale fragment behind.
      session.clear();
      toast.success(`Deleted ${result.deleted_count} records.`);
    } catch (caught) {
      toast.error(apiErrorMessage(caught, "Failed to clear history"));
    } finally {
      setClearing(false);
    }
  };

  // Filters the rows already fetched. Labelled as such, because the API has no
  // history search and claiming otherwise would be a lie about the scope.
  const needle = query.trim().toLowerCase();
  const visible = needle
    ? matches.filter((match) =>
        [match.candidate_name, match.cv_filename, match.job_title, match.company_name]
          .filter(Boolean)
          .some((field) => field!.toLowerCase().includes(needle))
      )
    : matches;

  const candidates = new Set(
    matches.map((match) => match.candidate_name || match.cv_filename || "unknown")
  );
  const average = matches.length
    ? matches.reduce((sum, match) => sum + match.final_score, 0) / matches.length
    : 0;

  return (
    <>
      <PageHeader
        title="Analysis history"
        subtitle="Every match written to the database, newest first."
        actions={
          matches.length > 0 ? (
            <button
              type="button"
              onClick={clear}
              disabled={clearing}
              className="btn-ghost border-error/30 text-error hover:bg-error/10"
            >
              {clearing ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <Trash2 className="h-4 w-4" aria-hidden />
              )}
              Clear history
            </button>
          ) : undefined
        }
      />

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard
          icon={Layers}
          label="Stored matches"
          value={total.toLocaleString()}
          hint="Rows in the database, across every run."
        />
        <StatCard
          icon={Users}
          label="Candidates loaded"
          value={candidates.size}
          hint="Distinct candidates among the rows fetched so far."
        />
        <StatCard
          icon={Gauge}
          label="Average score"
          value={`${average.toFixed(1)}%`}
          hint="Mean across the rows fetched so far, not the whole table."
        />
      </div>

      {error && matches.length === 0 ? (
        <ErrorState
          icon={WifiOff}
          title="Could not load history"
          message={error}
          onRetry={retry}
        />
      ) : !loading && matches.length === 0 ? (
        <EmptyState
          icon={HistoryIcon}
          title="Nothing stored yet"
          body="Matches are written here as résumés are analysed."
          action={{ label: "Analyse a résumé", href: "/upload" }}
        />
      ) : (
        <>
          <div className="relative mb-4 max-w-sm">
            <Search
              className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-tertiary"
              aria-hidden
            />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={`Filter the ${matches.length} loaded rows`}
              aria-label="Filter loaded history rows"
              className="field py-2 pl-11 text-sm"
            />
          </div>

          <div className="glass-panel overflow-hidden rounded-lg">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-white/5">
                  <tr>
                    {["Candidate", "Role", "Score", "Status", "Analysed"].map(
                      (heading) => (
                        <th
                          key={heading}
                          scope="col"
                          className="label-sm px-6 py-4 text-tertiary"
                        >
                          {heading}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {loading && matches.length === 0 ? (
                    Array.from({ length: 6 }, (_, index) => (
                      <RowSkeleton key={index} />
                    ))
                  ) : visible.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-6 py-12 text-center text-on-surface-variant"
                      >
                        No loaded row matches “{query}”.
                      </td>
                    </tr>
                  ) : (
                    visible.map((match) => (
                      <HistoryRow key={match.match_id} match={match} />
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between gap-4 border-t border-white/10 p-4">
              <span className="label-sm text-tertiary">
                Showing {visible.length} of {total.toLocaleString()}
              </span>
              {matches.length < total && (
                <button
                  type="button"
                  onClick={() => {
                    setLoading(true);
                    setPage((current) => current + 1);
                  }}
                  disabled={loading}
                  className="btn-ghost"
                >
                  {loading && (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                  )}
                  Load more
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}

function HistoryRow({ match }: { match: Match }) {
  const styles = bandStyles(match.final_score, match.status);
  const name = match.candidate_name || match.cv_filename || "Unknown candidate";

  return (
    <tr className="transition-colors hover:bg-white/5">
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-secondary-container/40 font-mono text-xs font-semibold text-secondary">
            {initials(name)}
          </span>
          <div className="min-w-0">
            <p className="truncate font-medium text-on-surface">{name}</p>
            {/* The document name when a live run recorded one. The CV's UUID
                is deliberately not shown: it identified nothing to a reader
                and printed a 36-character string under every row. */}
            {match.cv_filename && match.candidate_name && (
              <p className="truncate text-xs text-tertiary">{match.cv_filename}</p>
            )}
          </div>
        </div>
      </td>

      <td className="px-6 py-4">
        <Link
          href={`/jobs/${encodeURIComponent(match.job_id)}`}
          className="font-medium text-on-surface transition-colors hover:text-primary"
        >
          {match.job_title}
        </Link>
        <p className="truncate text-xs text-tertiary">
          {match.company_name}
          {match.location_city ? ` · ${match.location_city}` : ""}
        </p>
      </td>

      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-surface-container-highest">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.max(0, Math.min(100, match.final_score))}%`,
                backgroundColor: styles.hex,
              }}
            />
          </div>
          <span className={cn("font-semibold", styles.text)}>
            {Math.round(match.final_score)}%
          </span>
        </div>
      </td>

      <td className="px-6 py-4">
        <span className={cn("chip capitalize", styles.bg, styles.text)}>
          {match.status}
        </span>
      </td>

      <td className="px-6 py-4 text-sm text-tertiary">
        {formatDateTime(match.timestamp)}
      </td>
    </tr>
  );
}
