"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, SlidersHorizontal, ChevronDown, Loader2, SearchX, WifiOff } from "lucide-react";
import { getJobs, getJobFacets, apiErrorMessage } from "@/lib/api";
import type { Job, JobFacets, JobFilters } from "@/lib/types";
import { PageHeader } from "@/components/layout/page-header";
import { JobCard } from "@/components/jobs/job-card";
import { CardSkeletonGrid, EmptyState, ErrorState } from "@/components/ui/feedback";
import { titleCase } from "@/lib/utils";

const PAGE_SIZE = 12;
const SEARCH_DEBOUNCE_MS = 300;

export function JobsClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // The URL is the source of truth for the search term, so the top bar's quick
  // find can land here with a query already applied and the page is shareable.
  const [filters, setFilters] = useState<JobFilters>({
    search: searchParams.get("search") ?? "",
    category: searchParams.get("category") ?? "",
    remote_type: searchParams.get("remote_type") ?? "",
    seniority: searchParams.get("seniority") ?? "",
  });
  const [searchInput, setSearchInput] = useState(filters.search ?? "");

  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [corpusTotal, setCorpusTotal] = useState(0);
  const [facets, setFacets] = useState<JobFacets | null>(null);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Bumped by the retry button. Refetching by changing an input to the effect
  // keeps the fetch inside it, so nothing sets state synchronously during the
  // effect body and an unmount mid-flight cannot write to a dead component.
  const [reloadToken, setReloadToken] = useState(0);

  // Debounced: one request per pause in typing, not one per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      setFilters((prev) => ({ ...prev, search: searchInput }));
      setPage(0);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    getJobFacets()
      .then(setFacets)
      .catch(() => setFacets(null));
  }, []);

  useEffect(() => {
    // Cancels on cleanup, so an earlier request that resolves after a later
    // one cannot overwrite the current filter's results with a stale page.
    let cancelled = false;

    (async () => {
      try {
        const response = await getJobs(PAGE_SIZE, page * PAGE_SIZE, filters);
        if (cancelled) return;

        setError(null);
        setTotal(response.total);
        setCorpusTotal(response.corpus_total ?? response.total);
        setJobs((prev) => (page === 0 ? response.jobs : [...prev, ...response.jobs]));
      } catch (caught) {
        if (cancelled) return;
        setError(apiErrorMessage(caught, "Failed to load jobs"));
        if (page === 0) setJobs([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [page, filters, reloadToken]);

  const retry = () => {
    setLoading(true);
    setReloadToken((token) => token + 1);
  };

  // Keep the address bar in step with the active filters.
  useEffect(() => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value) params.set(key, value);
    }
    const query = params.toString();
    router.replace(query ? `/jobs?${query}` : "/jobs", { scroll: false });
  }, [filters, router]);

  const setFilter = (key: keyof JobFilters, value: string) => {
    setLoading(true);
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const clearAll = () => {
    setLoading(true);
    setSearchInput("");
    setFilters({ search: "", category: "", remote_type: "", seniority: "" });
    setPage(0);
  };

  const activeFilters = Object.values(filters).filter(Boolean).length;
  const hasMore = jobs.length < total;

  return (
    <>
      <PageHeader
        title="Job market"
        subtitle="Every role the matcher scores against, searchable by title, company, city and skill."
        meta={
          <p className="label-sm text-tertiary">
            {loading && page === 0
              ? "Searching…"
              : activeFilters > 0
                ? `${total.toLocaleString()} of ${corpusTotal.toLocaleString()} roles match`
                : `${corpusTotal.toLocaleString()} roles in the corpus`}
          </p>
        }
      />

      <div className="glass-panel mb-8 flex flex-col gap-4 rounded-lg p-4 lg:flex-row lg:items-center">
        <div className="relative w-full flex-1">
          <Search
            className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-primary"
            aria-hidden
          />
          <input
            type="search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by title, company, city or skill"
            aria-label="Search jobs"
            className="field pl-11"
          />
        </div>

        <div className="flex w-full flex-wrap gap-3 lg:w-auto lg:flex-nowrap">
          <FacetSelect
            label="Category"
            value={filters.category ?? ""}
            options={facets?.categories ?? []}
            onChange={(value) => setFilter("category", value)}
          />
          <FacetSelect
            label="Work model"
            value={filters.remote_type ?? ""}
            options={facets?.remote_types ?? []}
            onChange={(value) => setFilter("remote_type", value)}
          />
          <FacetSelect
            label="Seniority"
            value={filters.seniority ?? ""}
            options={facets?.seniority_levels ?? []}
            onChange={(value) => setFilter("seniority", value)}
          />

          {/* Only rendered when it has something to clear — a permanently
              disabled control is just noise on the toolbar. */}
          {activeFilters > 0 && (
            <button type="button" onClick={clearAll} className="btn-ghost shrink-0">
              <SlidersHorizontal className="h-4 w-4" aria-hidden />
              Clear {activeFilters}
            </button>
          )}
        </div>
      </div>

      {error && jobs.length === 0 ? (
        <ErrorState
          icon={WifiOff}
          title="Could not load the corpus"
          message={error}
          onRetry={retry}
        />
      ) : loading && page === 0 ? (
        <CardSkeletonGrid count={PAGE_SIZE} />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={SearchX}
          title="Nothing matches those filters"
          body={
            activeFilters > 0
              ? "Try a broader search, or clear a filter to widen the set."
              : "The corpus is empty. Check that data/json/jobs.json loaded on startup."
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <JobCard key={job.job_id} job={job} />
            ))}
          </div>

          {hasMore && (
            <div className="mt-12 flex justify-center">
              <button
                type="button"
                onClick={() => {
                  setLoading(true);
                  setPage((current) => current + 1);
                }}
                disabled={loading}
                className="btn-ghost rounded-full px-8 py-3"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                ) : (
                  <ChevronDown className="h-4 w-4" aria-hidden />
                )}
                {loading
                  ? "Loading…"
                  : `Load more (${(total - jobs.length).toLocaleString()} left)`}
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}

function FacetSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      aria-label={label}
      // Disabled until the facets arrive, rather than offering a hardcoded
      // list that can drift out of step with the corpus.
      disabled={options.length === 0}
      className="field min-w-[150px] flex-1 cursor-pointer py-3 capitalize disabled:cursor-not-allowed disabled:opacity-50 lg:flex-none"
    >
      <option value="">{label} (all)</option>
      {options.map((option) => (
        <option key={option} value={option}>
          {titleCase(option)}
        </option>
      ))}
    </select>
  );
}
