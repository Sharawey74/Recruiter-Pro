"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Search, Cpu, Menu } from "lucide-react";
import { checkHealth, API_BASE } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * The top app bar: a job search, and whether the service is answering.
 *
 * The reference design fills this side with a search field, a notification
 * bell, a settings gear and an account avatar. Three of those four have
 * nothing behind them — no notification stream, no settings surface, no
 * accounts — so shipping them would be shipping three dead buttons.
 *
 * It also carried a wordmark on the left, directly beside the sidebar's
 * "Recruiter Pro": the same name twice, a few inches apart, in two different
 * type treatments. Gone.
 *
 * The corpus size and scoring mode used to sit here as separate pills. Both
 * are properties of the engine rather than of this session — they do not
 * change while you work — so they crowded the bar with standing facts. The
 * landing page states them in context instead. What genuinely changes, and
 * what a user is affected by, is whether the backend is answering right now.
 */
export function TopBar({
  onOpenNav,
  navOpen = false,
}: {
  onOpenNav?: () => void;
  navOpen?: boolean;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [reachable, setReachable] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await checkHealth();
        if (cancelled) return;
        setHealth(data);
        setReachable(true);
      } catch {
        if (cancelled) return;
        setHealth(null);
        setReachable(false);
      }
    };

    poll();
    const interval = setInterval(poll, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const onSearch = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = query.trim();
    router.push(trimmed ? `/jobs?search=${encodeURIComponent(trimmed)}` : "/jobs");
  };

  const jobsLoaded = health?.components?.jobs_loaded ?? 0;
  const mlLoaded = health?.components?.ml_model_loaded;

  const detail =
    reachable === false
      ? "The backend did not answer its last health check. Start it with run.ps1"
      : reachable
        ? [
            `Connected to ${API_BASE}`,
            `${jobsLoaded.toLocaleString()} roles in the corpus`,
            mlLoaded
              ? "Hybrid scoring: ML model + rules"
              : "Rule-based scoring only — the ML model did not load",
          ].join(" · ")
        : "Contacting the backend…";

  return (
    // Left and right insets rather than a width calculation: `w-[calc(100%-16rem)]`
    // subtracted a sidebar that is not there below lg, leaving a 16rem strip of
    // page uncovered at the right of every phone screen.
    <header className="fixed inset-x-0 top-0 z-30 flex h-20 items-center justify-between gap-4 border-b border-white/10 bg-surface/40 px-margin-mobile backdrop-blur-xl md:px-margin-desktop lg:left-64 lg:justify-end lg:gap-6">
      {/*
        The drawer's only trigger, so it exists exactly where the drawer does.
        aria-expanded is what tells a screen reader this button owns something
        that is currently open.
      */}
      <button
        type="button"
        onClick={onOpenNav}
        aria-label="Open navigation"
        aria-expanded={navOpen}
        className="-ml-2 rounded p-2 text-on-surface-variant transition-colors hover:bg-primary/10 hover:text-primary lg:hidden"
      >
        <Menu className="h-6 w-6" aria-hidden />
      </button>

      <form onSubmit={onSearch} className="relative hidden lg:block" role="search">
        <Search
          className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-tertiary"
          aria-hidden
        />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Find a job…"
          aria-label="Search jobs by title, company or skill"
          className="w-64 rounded-full border border-outline-variant bg-surface-container py-2 pl-11 pr-4 text-sm text-on-surface placeholder-tertiary/50 transition-colors focus:border-secondary focus:outline-none"
        />
      </form>

      <div
        className={cn(
          "flex items-center gap-2.5 rounded-full border px-4 py-2 transition-colors",
          reachable === null && "border-white/10 bg-surface-container text-tertiary",
          reachable === true && "border-score-high/30 bg-score-high/10 text-score-high",
          reachable === false && "border-error/30 bg-error/10 text-error"
        )}
        title={detail}
      >
        {/* A live dot: the ring only pulses while the service is answering. */}
        <span className="relative flex h-2.5 w-2.5" aria-hidden>
          {reachable && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-score-high opacity-60" />
          )}
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-current" />
        </span>

        <span className="font-mono text-label-sm" aria-live="polite">
          {reachable === null ? "Connecting" : reachable ? "Live" : "Offline"}
        </span>

        {/*
          Surfaced only when it is bad news. A silent fall back to rule-based
          scoring produces numbers just as plausible as the hybrid path, so it
          has to be visible — but saying "hybrid" on every screen forever is
          noise, not information.
        */}
        {reachable && mlLoaded === false && (
          <span
            className="chip bg-score-medium/10 text-score-medium"
            title="The ML model did not load; scores come from rule-based matching alone."
          >
            <Cpu className="h-3 w-3" aria-hidden />
            rules only
          </span>
        )}
      </div>
    </header>
  );
}
