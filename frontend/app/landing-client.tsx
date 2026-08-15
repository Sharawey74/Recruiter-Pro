"use client";

import { useEffect, useRef, useState } from "react";
import { getStats } from "@/lib/api";
import type { Stats } from "@/lib/types";
import { cn } from "@/lib/utils";
import { usePrefersReducedMotion } from "@/components/landing/primitives";
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
 * Both in viewport heights, measured from the centre of the view to the centre
 * of a slide.
 *
 * The plateau is the important one. A slide that has come to rest anywhere
 * within a quarter of a viewport of centre is fully present -- so settling a
 * few pixels off, which proximity snapping allows and a trackpad guarantees,
 * cannot leave the page dimmed.
 */
const FULLY_IN_UNTIL = 0.25;
const FADE_OUT_AT = 0.85;

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
  const reduced = usePrefersReducedMotion();

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

  /*
   * How far each slide has entered, and which dot is lit, from the scroll
   * position itself.
   *
   * This was an IntersectionObserver reporting `intersectionRatio` into
   * `--enter`, with a 600ms CSS transition smoothing the steps between its 21
   * thresholds. Both halves of that were wrong.
   *
   * **The transition fought the scroll.** A transition interpolates towards a
   * target over its own duration. The target here changed on almost every
   * frame of a scroll, so each new value restarted the interpolation from
   * wherever the last one had reached, and the slides trailed the scroll by up
   * to 600ms instead of tracking it. Transitions are for values that change at
   * discrete moments; a scroll position is not one.
   *
   * **And the ratio was the wrong measure.** `intersectionRatio` is how much
   * of the slide is inside the container, which reaches 1.0 only when the two
   * are aligned to the pixel. That held while snapping was mandatory. Once it
   * became `proximity` -- so that a slide taller than the viewport could be
   * scrolled through -- a slide could come to rest slightly off, at a ratio of
   * 0.94, and sit there permanently at 96% opacity. Content that is quietly
   * dimmed for no reason is worse than content that does not animate.
   *
   * So: distance from the centre of the view, measured every frame, with a
   * plateau. Anything within a quarter of a viewport of centre is fully
   * present regardless of where the scroll settled; past that it ramps away.
   */
  useEffect(() => {
    const root = containerRef.current;
    if (!root) return;

    const slides = SLIDES.map(({ id }) => document.getElementById(id)).filter(
      (node): node is HTMLElement => node !== null
    );
    if (slides.length === 0) return;

    if (reduced) {
      for (const node of slides) node.style.setProperty("--enter", "1");
      return;
    }

    let frame = 0;
    let lit = -1;

    const measure = () => {
      frame = 0;

      // Every read first, then every write. Interleaving them makes the
      // browser flush layout between each pair, which is the classic way to
      // turn a cheap scroll handler into a slow one.
      const view = root.getBoundingClientRect();
      const centre = view.top + view.height / 2;
      const distances = slides.map((node) => {
        const rect = node.getBoundingClientRect();
        return Math.abs(rect.top + rect.height / 2 - centre) / view.height;
      });

      let closest = 0;
      for (let i = 0; i < distances.length; i++) {
        const enter = Math.max(
          0,
          Math.min(1, (FADE_OUT_AT - distances[i]!) / (FADE_OUT_AT - FULLY_IN_UNTIL))
        );
        slides[i]!.style.setProperty("--enter", enter.toFixed(3));
        if (distances[i]! < distances[closest]!) closest = i;
      }

      // React state only when the answer changes, which is three times over a
      // whole page rather than once a frame.
      if (closest !== lit) {
        lit = closest;
        setActive(closest);
      }
    };

    const onScroll = () => {
      // Coalesce to one measurement per frame. A scroll can fire several times
      // between paints and there is no point measuring twice for one picture.
      if (!frame) frame = requestAnimationFrame(measure);
    };

    measure();
    root.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);

    return () => {
      root.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(frame);
    };
  }, [reduced]);

  return (
    /*
     * `snap-proximity`, not `snap-mandatory`.
     *
     * Mandatory snapping always lands on a snap point, so when a slide is
     * taller than the container -- a short window, a zoomed-in browser, the map
     * slide at a laptop height -- the part of it hanging below the fold cannot
     * be reached: the scroll is pulled on to the next slide's start before it
     * gets there, and the content reads as cut off top and bottom. Proximity
     * keeps the settling behaviour when a slide roughly fills the view, and
     * gets out of the way when one does not fit.
     */
    <div
      ref={containerRef}
      // The negative margins cancel the shell's padding, so they have to track
      // it at every breakpoint: margin-mobile below md, margin-desktop above.
      className="-mx-margin-mobile -mb-16 -mt-28 h-[calc(100dvh-5rem)] snap-y snap-proximity overflow-y-auto overflow-x-hidden scroll-smooth md:-mx-margin-desktop"
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
