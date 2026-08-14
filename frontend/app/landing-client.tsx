"use client";

import { useEffect, useRef, useState } from "react";
import { getStats } from "@/lib/api";
import type { Stats } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  HeroSlide,
  ParsingSlide,
  ReachSlide,
  CtaSlide,
} from "@/components/landing/slides";

const SLIDES = [
  { id: "neural-matching", label: "Neural matching" },
  { id: "intelligent-parsing", label: "Intelligent parsing" },
  { id: "global-reach", label: "Global reach" },
  { id: "get-started", label: "Get started" },
] as const;

/**
 * The landing page: four scroll-snapped slides inside the app shell.
 *
 * The snap container is this element rather than the document, because the
 * page sits inside a fixed sidebar and top bar. Snapping the document would
 * fight the shell — and `scroll-snap-type` on `body` is unreliable when an
 * ancestor is already a scroll container.
 *
 * The negative margins cancel the padding the root layout applies to every
 * other page. Slides are full-bleed by definition; the alternative is a route
 * group with a second layout, which would duplicate the shell to change one
 * padding rule.
 */
export function LandingClient() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [active, setActive] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const data = await getStats();
        if (!cancelled) setStats(data);
      } catch {
        // The page renders without figures rather than showing an error: this
        // is the first thing a visitor sees, and a dead API is not their
        // problem. The slides fall back to zeroes and the copy still reads.
        if (!cancelled) setStats(null);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  // Which slide the dot rail highlights.
  useEffect(() => {
    const root = containerRef.current;
    if (!root) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const index = SLIDES.findIndex((s) => s.id === entry.target.id);
          if (index >= 0) setActive(index);
        }
      },
      { root, threshold: 0.5 }
    );

    for (const slide of SLIDES) {
      const node = document.getElementById(slide.id);
      if (node) observer.observe(node);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className="-mx-margin-desktop -mb-16 -mt-28 h-[calc(100vh-5rem)] snap-y snap-mandatory overflow-y-auto overflow-x-hidden scroll-smooth"
    >
      <HeroSlide stats={stats} />
      <ParsingSlide stats={stats} />
      <ReachSlide stats={stats} />
      <CtaSlide stats={stats} />

      {/* Slide rail. Real navigation, not decoration: each dot scrolls. */}
      <nav
        className="fixed right-6 top-1/2 z-20 hidden -translate-y-1/2 flex-col gap-3 lg:flex"
        aria-label="Landing sections"
      >
        {SLIDES.map((slide, index) => (
          <a
            key={slide.id}
            href={`#${slide.id}`}
            aria-label={slide.label}
            aria-current={active === index ? "true" : undefined}
            className={cn(
              "h-2.5 w-2.5 rounded-full border transition-all duration-300",
              active === index
                ? "scale-125 border-primary bg-primary shadow-glow"
                : "border-white/25 bg-transparent hover:border-primary/60"
            )}
          />
        ))}
      </nav>
    </div>
  );
}
