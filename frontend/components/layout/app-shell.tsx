"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";

/**
 * The application frame, and the one place that knows whether the navigation
 * drawer is open.
 *
 * The shell used to be three siblings in the root layout: a `fixed w-64`
 * sidebar, a top bar sized `calc(100% - 16rem)`, and a `main` with a hard
 * `ml-64`. None of those had a breakpoint, so below roughly 700px the sidebar
 * covered most of the screen and the content was squeezed into what was left --
 * at 420px the jobs toolbar had 84px to work in. The layout did not degrade on
 * a phone; it stopped working.
 *
 * Below `lg` the sidebar is a drawer instead, and the content takes the full
 * width. That needs open/closed state shared between the button in the top bar
 * and the drawer itself, which is what this component exists for. It is a
 * client component, but `children` are passed in as a prop from the root
 * layout, so the pages inside it stay server components.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const [navOpen, setNavOpen] = useState(false);
  const close = () => setNavOpen(false);

  // Escape closes it. Anything that traps the viewport needs a way out that is
  // not "find the small button".
  useEffect(() => {
    if (!navOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setNavOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navOpen]);

  // Hold the page still underneath. Without this the drawer sits over a page
  // that scrolls with it, which reads as the drawer itself sliding.
  useEffect(() => {
    if (!navOpen) return;

    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [navOpen]);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar open={navOpen} onNavigate={close} onClose={close} />

      {/*
        Rendered at all times rather than mounted with the drawer, so it can
        fade. `pointer-events-none` when closed is what keeps an invisible
        full-screen div from swallowing every click on the page.
      */}
      <div
        onClick={close}
        aria-hidden
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 lg:hidden ${
          navOpen ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />

      <TopBar onOpenNav={() => setNavOpen(true)} navOpen={navOpen} />

      {/* ml only from lg, where the sidebar is permanent. pt-28 clears the
          fixed top bar at every width. */}
      <main className="px-margin-mobile pb-16 pt-28 md:px-margin-desktop lg:ml-64">
        <div className="mx-auto w-full max-w-container">{children}</div>
      </main>
    </div>
  );
}
