"use client";

import Link from "next/link";
import {
  ArrowRight,
  ArrowDown,
  Play,
  ScanText,
  KeyRound,
  Cpu,
  MessageSquareText,
  Globe2,
  Building2,
  MapPin,
  Layers,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import type { Stats } from "@/lib/types";
import { cn } from "@/lib/utils";
import { CountUp, ParticleField, Reveal, Slide } from "./primitives";

/**
 * The four landing slides.
 *
 * Every figure on this page comes from GET /stats, measured against the
 * running corpus. The reference design specified 99% Accuracy, 10x Faster,
 * 50M+ Profiles, 1,204 Job Boards, 5.4M+ Candidate Profiles, 500+ recruiting
 * teams and a logo wall of four companies. None of those are true of this
 * system, and one is worse than untrue: TASKS.md 1.4 records that the
 * classifier's 99% is an artifact of a synthetic label that two ordinary
 * columns reproduce, and that the finding is the most valuable thing in the
 * repository. Advertising the number would contradict the analysis.
 *
 * The substitutions keep the shape of the design and change the content to
 * things the corpus can support: 800 roles, 27 countries, 654 distinct skills,
 * a 679-skill vocabulary, and a measured 22x speed-up. They are also simply
 * better copy — an engineer reading "5.4M+ profiles" on a portfolio project
 * discounts everything after it.
 */

// Measured in Phase 3: 16.64s -> 0.74s per upload against the same corpus.
const SPEEDUP = 22;
const SECONDS_PER_CV = 0.74;

export function HeroSlide({ stats }: { stats: Stats | null }) {
  return (
    <Slide id="neural-matching" className="landing-grid">
      {/* Ambient wash behind the grid, drifting slowly. */}
      <div
        className="pointer-events-none absolute -left-40 top-10 h-[28rem] w-[28rem] rounded-full bg-primary/10 blur-[120px]"
        style={{ animation: "landing-float 18s ease-in-out infinite" }}
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -right-32 bottom-0 h-[24rem] w-[24rem] rounded-full bg-secondary-container/10 blur-[120px]"
        style={{ animation: "landing-float 22s ease-in-out infinite reverse" }}
        aria-hidden
      />
      <ParticleField />

      <div className="relative flex flex-col items-center gap-8 text-center">
        <Reveal delayMs={80}>
          <h1 className="text-balance font-bold leading-[1.05] tracking-tight text-on-surface"
            style={{ fontSize: "clamp(2.25rem, 5.5vw, 4.5rem)" }}>
            The future of
            <br />
            <span className="bg-gradient-to-r from-primary via-primary-fixed to-secondary bg-clip-text text-transparent">
              talent acquisition
            </span>
          </h1>
        </Reveal>

        <Reveal delayMs={160}>
          <p className="max-w-2xl text-on-surface-variant"
            style={{ fontSize: "clamp(1rem, 1.35vw, 1.25rem)" }}>
            Parse a résumé, extract its skills against a curated taxonomy, and
            score it against every open role — in one pass, with the reasoning
            shown rather than asserted.
          </p>
        </Reveal>

        <Reveal delayMs={240}>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href="/upload" className="btn-primary text-base">
              Analyse a résumé
              <ArrowRight className="h-5 w-5" aria-hidden />
            </Link>
            <Link href="/jobs" className="btn-secondary text-base">
              <Play className="h-5 w-5" aria-hidden />
              Browse the corpus
            </Link>
          </div>
        </Reveal>

        <Reveal delayMs={320} className="w-full">
          <dl
            className="mt-8 grid w-full gap-8 border-t border-white/10 pt-10"
            style={{ gridTemplateColumns: "repeat(auto-fit, minmax(9rem, 1fr))" }}
          >
            <Stat
              value={stats?.corpus.jobs ?? 0}
              label="Roles indexed"
              hint="Live count from the corpus the matcher scores against."
            />
            <Stat
              value={SPEEDUP}
              suffix="×"
              label="Faster"
              hint="Measured: 16.64s to 0.74s per upload, after batching the scoring pass."
            />
            <Stat
              value={stats?.corpus.distinct_skills ?? 0}
              label="Distinct skills"
              hint="Unique skills across every job posting in the corpus."
            />
            <Stat
              value={SECONDS_PER_CV}
              decimals={2}
              suffix="s"
              label="Per résumé"
              hint="End-to-end, all four agents, against the full corpus."
            />
          </dl>
        </Reveal>
      </div>

      <a
        href="#intelligent-parsing"
        className="absolute bottom-6 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2 text-tertiary transition-colors hover:text-primary"
      >
        <span className="label-sm">Discover</span>
        <ArrowDown
          className="h-4 w-4"
          style={{ animation: "landing-float 2.4s ease-in-out infinite" }}
          aria-hidden
        />
      </a>
    </Slide>
  );
}

function Stat({
  value,
  label,
  hint,
  suffix,
  decimals = 0,
}: {
  value: number;
  label: string;
  hint: string;
  suffix?: string;
  decimals?: number;
}) {
  return (
    <div className="text-center" title={hint}>
      <dd className="font-bold text-on-surface"
        style={{ fontSize: "clamp(1.85rem, 3.2vw, 3rem)" }}>
        <CountUp value={value} decimals={decimals} suffix={suffix} />
      </dd>
      <dt className="label-sm mt-2 text-tertiary">{label}</dt>
    </div>
  );
}

/**
 * The four agents, described by what they do.
 *
 * The design's copy claimed "discerning true seniority from inflated job
 * titles" and "validating credentials against global indices". The extractor
 * matches a curated alias index; it does neither of those. Describing capacity
 * the system lacks is the same defect as a dead button, one layer up.
 */
const PIPELINE: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: ScanText,
    title: "Document parsing",
    body: "PDF, DOCX and plain text reduced to a clean text layer, with the file's real bytes checked against its extension before anything reads it.",
  },
  {
    icon: KeyRound,
    title: "Skill extraction",
    body: "Skills resolved against one canonical vocabulary rather than matched literally, so React, ReactJS and React.js all land on the same skill.",
  },
  {
    icon: Cpu,
    title: "Hybrid scoring",
    body: "Five weighted rule-based components — skills, title, experience, education, keywords — blended with a trained classifier, each reported separately.",
  },
  {
    icon: MessageSquareText,
    title: "Explanation",
    body: "A written rationale per match, tagged with the provider that produced it, falling back to a rule-based writer when no model is reachable.",
  },
];

export function ParsingSlide({ stats }: { stats: Stats | null }) {
  return (
    <Slide id="intelligent-parsing">
      <div className="flex flex-col gap-10">
        <Reveal>
          <span className="chip border border-primary/30 bg-primary/10 text-primary">
            <Sparkles className="h-3.5 w-3.5" aria-hidden />
            Intelligent parsing
          </span>
        </Reveal>

        <Reveal delayMs={80}>
          <h2 className="max-w-3xl text-balance font-bold tracking-tight text-on-surface"
            style={{ fontSize: "clamp(2rem, 4.5vw, 3.75rem)" }}>
            Beyond keywords.
          </h2>
        </Reveal>

        <Reveal delayMs={140}>
          <p className="max-w-3xl text-lg text-on-surface-variant md:text-xl">
            Four agents, each with one job and a defined contract between them.
            {stats && (
              <>
                {" "}
                The vocabulary carries{" "}
                <strong className="text-on-surface">
                  {stats.engine.canonical_skills.toLocaleString()}
                </strong>{" "}
                canonical skills behind{" "}
                <strong className="text-on-surface">
                  {stats.engine.skill_aliases.toLocaleString()}
                </strong>{" "}
                aliases.
              </>
            )}
          </p>
        </Reveal>

        <div
          className="grid gap-6"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(15rem, 1fr))" }}
        >
          {PIPELINE.map(({ icon: Icon, title, body }, index) => (
            <Reveal key={title} delayMs={200 + index * 90}>
              <article className="landing-conic-card card-interactive group h-full border border-transparent p-6">
                <span className="mb-5 flex h-12 w-12 items-center justify-center rounded-md border border-white/5 bg-surface-container-highest">
                  <Icon
                    className="h-6 w-6 text-primary transition-transform duration-300 group-hover:scale-110"
                    aria-hidden
                  />
                </span>
                <h3 className="mb-2 text-lg font-semibold text-on-surface">
                  {title}
                </h3>
                <p className="text-sm leading-relaxed text-on-surface-variant">
                  {body}
                </p>
              </article>
            </Reveal>
          ))}
        </div>

        <Reveal delayMs={560}>
          <Link href="/dashboard" className="btn-secondary w-fit">
            See it run
            <ArrowRight className="h-5 w-5" aria-hidden />
          </Link>
        </Reveal>
      </div>
    </Slide>
  );
}

/**
 * Global reach, from the corpus's own geography.
 *
 * The design asked for 1,204 job boards and 5.4M candidate profiles over a
 * world map. There is one corpus and no candidate database — but the corpus is
 * genuinely international, so the map plots the countries actually in it, with
 * their real counts. The visual survives; the numbers become checkable.
 */
export function ReachSlide({ stats }: { stats: Stats | null }) {
  const top = stats?.corpus.top_countries ?? [];
  const busiest = top[0]?.jobs ?? 1;

  return (
    <Slide id="global-reach">
      <div className="grid grid-cols-12 gap-gutter">
        <div className="col-span-12 flex flex-col gap-6 lg:col-span-5">
          <Reveal>
            <span className="chip border border-secondary/30 bg-secondary/10 text-secondary">
              <Globe2 className="h-3.5 w-3.5" aria-hidden />
              Global reach
            </span>
          </Reveal>

          <Reveal delayMs={80}>
            <h2 className="text-balance font-bold tracking-tight text-on-surface"
              style={{ fontSize: "clamp(1.75rem, 3.4vw, 3rem)" }}>
              Roles across {stats?.corpus.countries ?? 0} countries
            </h2>
          </Reveal>

          <Reveal delayMs={140}>
            <p className="text-lg text-on-surface-variant">
              Every posting the matcher scores against, drawn from{" "}
              {stats?.corpus.companies ?? 0} companies in{" "}
              {stats?.corpus.cities ?? 0} cities. These are counts from the
              loaded corpus, not projections.
            </p>
          </Reveal>

          <div className="grid grid-cols-3 gap-4">
            {[
              { icon: Globe2, value: stats?.corpus.countries ?? 0, label: "Countries" },
              { icon: MapPin, value: stats?.corpus.cities ?? 0, label: "Cities" },
              { icon: Building2, value: stats?.corpus.companies ?? 0, label: "Companies" },
            ].map(({ icon: Icon, value, label }, index) => (
              <Reveal key={label} delayMs={200 + index * 80}>
                <div className="glass-panel card-interactive rounded-lg p-4 text-center">
                  <Icon className="mx-auto mb-2 h-5 w-5 text-secondary" aria-hidden />
                  <p className="text-2xl font-bold text-on-surface">
                    <CountUp value={value} />
                  </p>
                  <p className="label-sm mt-1 text-tertiary">{label}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        {/*
          A ranked bar chart rather than a decorative world map. A map would
          need a projection and per-country coordinates to be honest about
          where anything is; the bars carry the same information — which
          markets the corpus actually covers — without inventing geography.
        */}
        <div className="col-span-12 lg:col-span-7">
          <Reveal delayMs={220}>
            <div className="glass-panel rounded-lg p-6">
              <div className="mb-6 flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-headline-md text-on-surface">
                  <Layers className="h-5 w-5 text-primary" aria-hidden />
                  Roles by market
                </h3>
                <span className="label-sm text-tertiary">
                  top {top.length} of {stats?.corpus.countries ?? 0}
                </span>
              </div>

              <ul className="space-y-3">
                {top.map(({ country, jobs }, index) => (
                  <li key={country} className="flex items-center gap-4">
                    <span className="w-36 shrink-0 truncate text-sm text-on-surface-variant">
                      {country}
                    </span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-container-highest">
                      <div
                        className={cn(
                          "h-full rounded-full",
                          index === 0
                            ? "bg-primary"
                            : index < 3
                              ? "bg-secondary"
                              : "bg-tertiary/70"
                        )}
                        style={{
                          width: `${Math.round((jobs / busiest) * 100)}%`,
                          transformOrigin: "left",
                          // `forwards`, not `both`: with `both` the bar holds
                          // scaleX(0) through its stagger delay and stays
                          // collapsed forever if the animation never runs. The
                          // failure mode here is a bar that appears without
                          // growing, which is the right way round.
                          animation: `landing-grow 900ms cubic-bezier(0.16, 1, 0.3, 1) ${
                            index * 60
                          }ms forwards`,
                        }}
                      />
                    </div>
                    <span className="w-10 shrink-0 text-right font-mono text-xs text-tertiary">
                      {jobs}
                    </span>
                  </li>
                ))}

                {top.length === 0 && (
                  <li className="py-8 text-center text-on-surface-variant">
                    No corpus loaded — start the API to populate this.
                  </li>
                )}
              </ul>
            </div>
          </Reveal>
        </div>
      </div>
    </Slide>
  );
}

export function CtaSlide({ stats }: { stats: Stats | null }) {
  return (
    <Slide id="get-started" className="items-center text-center">
      {/* A line sweeping down the slide. */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-transparent via-primary/10 to-transparent"
        style={{ animation: "landing-scan 6s linear infinite" }}
        aria-hidden
      />

      <Reveal>
        <div className="glass-panel mx-auto max-w-3xl rounded-xl px-8 py-16">
          <h2 className="text-balance font-bold tracking-tight text-on-surface"
              style={{ fontSize: "clamp(1.75rem, 3.4vw, 3rem)" }}>
            Ready to see it work?
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-lg text-on-surface-variant">
            Drop in a résumé and watch it scored against all{" "}
            {stats?.corpus.jobs.toLocaleString() ?? "800"} roles — with every
            component of every score, and the gaps, shown.
          </p>

          <Link
            href="/dashboard"
            className="btn-primary group mx-auto mt-10 w-fit rounded-full px-12 py-5 text-lg
                       transition-transform duration-300 hover:scale-[1.04] active:scale-[0.98]"
            style={{ animation: "landing-pulse-glow 2.8s ease-in-out infinite" }}
          >
            Enter the dashboard
            <ArrowRight
              className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
              aria-hidden
            />
          </Link>

        </div>
      </Reveal>
    </Slide>
  );
}
