"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { cn } from "@/lib/utils";

/**
 * Shared behaviour for the landing slides: scroll-triggered reveals, counters
 * that tick up, and the particle field behind the hero.
 *
 * Everything here is inert when the OS asks for reduced motion. That is not
 * politeness — a full-screen particle canvas and four simultaneous infinite
 * animations are exactly what triggers vestibular symptoms, and this page is
 * the first thing a visitor sees.
 */

const MOTION_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeToMotionPreference(onChange: () => void): () => void {
  const query = window.matchMedia(MOTION_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/**
 * The OS "reduce motion" setting, as an external store.
 *
 * A media query is exactly what useSyncExternalStore is for: reading it into
 * component state inside an effect means a second render before paint, and the
 * server has no matchMedia at all. getServerSnapshot returns false so the
 * markup renders identically on both sides and the real value takes over at
 * hydration.
 */
export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(
    subscribeToMotionPreference,
    () => window.matchMedia(MOTION_QUERY).matches,
    () => false
  );
}

/**
 * Reveals children once they enter the viewport.
 *
 * IntersectionObserver rather than a scroll handler: a scroll listener fires on
 * every frame of a scroll and has to measure the element itself, which forces
 * layout. The observer reports the same thing off the main thread.
 */
export function Reveal({
  children,
  delayMs = 0,
  className,
}: {
  children: ReactNode;
  delayMs?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    let stagger = 0;
    const reveal = () => {
      delete node.dataset.pending;
      node.dataset.revealed = "true";
    };
    const revealAfterDelay = () => {
      stagger = window.setTimeout(reveal, delayMs);
    };

    if (typeof IntersectionObserver === "undefined") {
      reveal();
      return;
    }

    // Hide only now that we know something will show it again.
    node.dataset.pending = "true";

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          revealAfterDelay();
          // Once revealed, stop watching. Re-animating on every scroll past is
          // the difference between a considered entrance and a nervous tic.
          observer.disconnect();
        }
      },
      { threshold: 0.15 }
    );
    observer.observe(node);

    // Safety net. An observer inside a scroll container can legitimately never
    // fire -- a slide the visitor never reaches, a browser that throttles
    // observers in a background tab. Content that is merely un-animated is
    // fine; content that is permanently invisible is not.
    const failsafe = window.setTimeout(reveal, 2500);

    return () => {
      observer.disconnect();
      window.clearTimeout(failsafe);
      window.clearTimeout(stagger);
    };
  }, [delayMs]);

  return (
    <div ref={ref} className={cn("landing-reveal", className)}>
      {children}
    </div>
  );
}

/**
 * A number that counts up the first time it is seen.
 *
 * Driven by requestAnimationFrame against a wall-clock start, not a fixed
 * increment per tick: a setInterval counter runs at a different speed on a
 * loaded machine, and lands on the wrong number if a frame is dropped.
 */
export function CountUp({
  value,
  durationMs = 1400,
  decimals = 0,
  suffix = "",
  prefix = "",
}: {
  value: number;
  durationMs?: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
}) {
  const [shown, setShown] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const reduced = usePrefersReducedMotion();

  const format = useCallback(
    (n: number) =>
      `${prefix}${n.toLocaleString("en-GB", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}${suffix}`,
    [prefix, suffix, decimals]
  );

  useEffect(() => {
    // Nothing to animate; the render below shows the final value directly
    // rather than setting state here, which would be a synchronous setState
    // in an effect body.
    if (reduced) return;

    const node = ref.current;
    if (!node) return;

    let frame = 0;
    let settle = 0;

    // Same reasoning as the reveal failsafe: an observer that never fires --
    // a slide never scrolled to, a throttled tab -- must not leave "0" sitting
    // under a label that reads ROLES INDEXED.
    const failsafe = window.setTimeout(() => setShown(value), 3000);

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();

        // If requestAnimationFrame never runs -- a throttled background tab,
        // a headless renderer -- the number must still arrive. Landing on the
        // right figure late beats showing zero forever.
        settle = window.setTimeout(() => setShown(value), durationMs + 600);

        const startedAt = performance.now();
        const tick = (now: number) => {
          const progress = Math.min(1, (now - startedAt) / durationMs);
          // Ease-out cubic: fast at first, settling on the final figure rather
          // than crawling into it.
          const eased = 1 - Math.pow(1 - progress, 3);
          setShown(value * eased);
          if (progress < 1) frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
      },
      { threshold: 0.4 }
    );

    observer.observe(node);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
      window.clearTimeout(settle);
      window.clearTimeout(failsafe);
    };
  }, [value, durationMs, reduced]);

  // The final value is in the DOM for assistive tech and for anyone who lands
  // mid-animation; only the visible text interpolates.
  return (
    <span ref={ref} aria-label={format(value)}>
      <span aria-hidden>{format(reduced ? value : shown)}</span>
    </span>
  );
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  alpha: number;
}

/**
 * Drifting points with a glow that follows the cursor.
 *
 * Canvas rather than DOM nodes: sixty absolutely-positioned divs each with
 * their own animation is sixty things for the compositor to track, and it
 * shows on a laptop. One canvas is one layer.
 *
 * The loop stops when the canvas leaves the viewport, so scrolling to slide
 * four does not leave an animation burning CPU behind it.
 */
export function ParticleField({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    if (reduced) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    let width = 0;
    let height = 0;
    let particles: Particle[] = [];
    let frame = 0;
    let running = false;
    const pointer = { x: -9999, y: -9999 };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      // Cap the device pixel ratio at 2: a 3x phone display triples the pixels
      // to shade for no visible gain on a field of soft dots.
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = Math.floor(width * ratio);
      canvas.height = Math.floor(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);

      // Density by area, so a wide monitor is not sparse and a phone is not
      // a soup. Capped, because the count is the cost.
      const count = Math.min(90, Math.round((width * height) / 16000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.22,
        vy: (Math.random() - 0.5) * 0.22,
        radius: Math.random() * 1.6 + 0.5,
        alpha: Math.random() * 0.4 + 0.15,
      }));
    };

    const draw = () => {
      context.clearRect(0, 0, width, height);

      // The cursor glow, drawn under the points.
      if (pointer.x > -9999) {
        const glow = context.createRadialGradient(
          pointer.x, pointer.y, 0,
          pointer.x, pointer.y, 220
        );
        glow.addColorStop(0, "rgba(208, 188, 255, 0.16)");
        glow.addColorStop(1, "rgba(208, 188, 255, 0)");
        context.fillStyle = glow;
        context.fillRect(pointer.x - 220, pointer.y - 220, 440, 440);
      }

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;

        // Wrap rather than bounce: a bounce makes the edges of the field
        // visible as a boundary, which gives away that it is a box.
        if (p.x < -10) p.x = width + 10;
        if (p.x > width + 10) p.x = -10;
        if (p.y < -10) p.y = height + 10;
        if (p.y > height + 10) p.y = -10;

        context.beginPath();
        context.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        context.fillStyle = `rgba(208, 188, 255, ${p.alpha})`;
        context.fill();
      }

      frame = requestAnimationFrame(draw);
    };

    const start = () => {
      if (running) return;
      running = true;
      frame = requestAnimationFrame(draw);
    };
    const stop = () => {
      running = false;
      cancelAnimationFrame(frame);
    };

    const onPointerMove = (event: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = event.clientX - rect.left;
      pointer.y = event.clientY - rect.top;
    };
    const onPointerLeave = () => {
      pointer.x = -9999;
      pointer.y = -9999;
    };

    resize();

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);

    // Only animate while on screen.
    const visibility = new IntersectionObserver(
      ([entry]) => (entry?.isIntersecting ? start() : stop()),
      { threshold: 0 }
    );
    visibility.observe(canvas);

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerleave", onPointerLeave);

    return () => {
      stop();
      resizeObserver.disconnect();
      visibility.disconnect();
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerleave", onPointerLeave);
    };
  }, [reduced]);

  return (
    <canvas
      ref={canvasRef}
      className={cn("pointer-events-none absolute inset-0 h-full w-full", className)}
      aria-hidden
    />
  );
}

/** A full-height snap target. Every slide is one of these. */
export function Slide({
  id,
  children,
  className,
}: {
  id: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      id={id}
      className={cn(
        "landing-slide relative flex min-h-[calc(100vh-5rem)] w-full flex-col justify-center overflow-hidden px-margin-desktop py-16",
        className
      )}
    >
      <div className="mx-auto w-full max-w-container">{children}</div>
    </section>
  );
}
