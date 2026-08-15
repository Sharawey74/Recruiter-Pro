"use client";

import { useEffect, useRef, useState } from "react";
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

  // The search term the last fetch actually used. Held in a ref because it is
  // not rendered — it exists to stop the debounce below from committing a value
  // that is already committed.
  const committedSearch = useRef(filters.search ?? "");

  // Debounced: one request per pause in typing, not one per keystroke.
  //
  // The equality check is what keeps it to one. Without it the timer fired
  // once on mount and re-committed the initial term as a new object, so every
  // visit to this page fetched the first results twice and put a loading
  // skeleton over the results it had just rendered.
  useEffect(() => {
    if (searchInput === committedSearch.current) return;

    const timer = setTimeout(() => {
      committedSearch.current = searchInput;
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
    // Committed here as well as in state, or the debounce would see a changed
    // input a moment later and fetch the same empty search a second time.
    committedSearch.current = "";
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

      {/*
        One wrapping row of flex items with explicit bases, rather than a row
        containing a nested row.

        The nested version overflowed the page. `.field` carries `w-full`, and
        the selects were `lg:flex-none` — flex-none means flex-basis: auto,
        which defers to that width: 100%. Each of the three selects therefore
        asked for the full width of the row it was in, the row asked for three
        times its own width, and the toolbar ran off the right of the screen
        with the last filter past the edge. Zooming out made it worse, not
        better, because the wider the container the wider each 100%.

        Every item here declares its own flex-basis, which takes precedence over
        that width, so nothing is sized by a percentage of its container and
        nothing can be sized by its own contents. `flex-wrap` handles the rest:
        the filters drop under the search field when the row runs out of room,
        at any zoom level, with no breakpoint involved.
      */}
      <div className="glass-panel mb-8 flex flex-wrap items-center gap-3 rounded-lg p-4">
        <div className="relative min-w-0 flex-[3_1_18rem]">
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
      // min-w-0 matters as much as the basis: a flex item's default minimum is
      // its min-content width, and for a <select> that is the widest option it
      // holds. Without it, one long category name sets the floor for the whole
      // toolbar.
      // The max-width is for the wrapped case: a filter that ends up alone on
      // its row would otherwise grow to the full width of the toolbar, which
      // reads as a mistake next to two normal-sized ones above it.
      className="field min-w-0 max-w-[20rem] flex-[1_1_10rem] cursor-pointer py-3 capitalize disabled:cursor-not-allowed disabled:opacity-50"
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
