"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Search, Activity, Database, Cpu } from "lucide-react";
import { checkHealth } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * The top app bar.
 *
 * The reference design fills the right-hand side with a search field, a
 * notification bell, a settings gear and an account avatar. Three of those
 * four have nothing behind them: this application has no notification stream,
 * no settings surface and no accounts. Shipping them would be shipping three
 * buttons that do nothing, which the brief rules out.
 *
 * The slot is the same size and holds live system state instead — the three
 * facts that actually change and that a user is affected by. The search field
 * stays, because it can be made real: it is the Jobs filter.
 */
export function TopBar() {
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

  return (
    <header className="fixed right-0 top-0 z-30 flex h-20 w-[calc(100%-16rem)] items-center justify-between gap-6 border-b border-white/10 bg-surface/40 px-margin-desktop backdrop-blur-xl">
      <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-headline-lg font-bold text-transparent">
        Recruiter Pro
      </span>

      <div className="flex items-center gap-6">
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

        <div className="flex items-center gap-2">
          <StatusChip
            icon={Activity}
            tone={reachable === null ? "idle" : reachable ? "ok" : "bad"}
            label={
              reachable === null
                ? "Checking…"
                : reachable
                ? "API online"
                : "API offline"
            }
            title={
              reachable
                ? "The backend answered its last health check."
                : "The backend did not answer. Start it with: uvicorn src.api:app --reload"
            }
          />

          {reachable && (
            <>
              <StatusChip
                icon={Database}
                tone={jobsLoaded > 0 ? "ok" : "bad"}
                label={`${jobsLoaded.toLocaleString()} jobs`}
                title={
                  jobsLoaded > 0
                    ? "Jobs currently loaded in the matching corpus."
                    : "No corpus loaded — every match request will return 503."
                }
                className="hidden md:inline-flex"
              />

              {/* Whether the advertised hybrid scoring is actually running.
                  Both paths return plausible numbers, so a silent fallback to
                  rules-only is invisible unless it is stated. */}
              <StatusChip
                icon={Cpu}
                tone={mlLoaded ? "ok" : "warn"}
                label={mlLoaded ? "Hybrid" : "Rules only"}
                title={
                  mlLoaded
                    ? "Scores blend the ML model with rule-based matching."
                    : "The ML model did not load. Scores come from rule-based matching alone."
                }
                className="hidden md:inline-flex"
              />
            </>
          )}
        </div>
      </div>
    </header>
  );
}

const TONES = {
  ok: "bg-score-high/10 text-score-high",
  warn: "bg-score-medium/10 text-score-medium",
  bad: "bg-error/10 text-error",
  idle: "bg-surface-container text-tertiary",
} as const;

function StatusChip({
  icon: Icon,
  tone,
  label,
  title,
  className,
}: {
  icon: typeof Activity;
  tone: keyof typeof TONES;
  label: string;
  title: string;
  className?: string;
}) {
  return (
    <span className={cn("chip", TONES[tone], className)} title={title}>
      <Icon className="h-3.5 w-3.5" aria-hidden />
      <span aria-live="polite">{label}</span>
    </span>
  );
}
