"use client";

import { useSyncExternalStore } from "react";

/**
 * A media query, as an external store.
 *
 * This is what useSyncExternalStore is for. Reading a query into component
 * state inside an effect means a second render before paint, and the server has
 * no matchMedia at all — so the server snapshot is a fixed value and the real
 * one takes over at hydration, with no mismatch in between.
 *
 * The subscription is created per call rather than cached per query string.
 * Both callers here are mounted once for the lifetime of the page; a cache
 * would be bookkeeping for a cost nobody is paying.
 */
export function useMediaQuery(query: string, serverValue = false): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const list = window.matchMedia(query);
      list.addEventListener("change", onChange);
      return () => list.removeEventListener("change", onChange);
    },
    () => window.matchMedia(query).matches,
    () => serverValue
  );
}

/** Tailwind's `lg`. The width at which the sidebar stops being a drawer. */
export const DESKTOP_QUERY = "(min-width: 1024px)";

/**
 * Whether the sidebar is permanent rather than a drawer.
 *
 * Defaults to false on the server, so the first paint treats the sidebar as a
 * closed drawer. That is the safe direction: a desktop visitor gets a sidebar
 * that is inert for the few milliseconds before hydration, during which nothing
 * on the page is interactive anyway. The reverse default would put seven
 * focusable links off the left edge of every phone.
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(DESKTOP_QUERY);
}
