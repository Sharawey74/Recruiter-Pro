"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  LayoutDashboard,
  FileUp,
  Briefcase,
  BarChart3,
  History,
  Star,
  ScanLine,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIsDesktop } from "@/lib/media";

/**
 * Primary navigation.
 *
 * Every route the app serves is here. Two of them — /jobs and /upload — had
 * pages, were fully built, and appeared in no menu, so the only way to reach
 * them was to type the URL.
 *
 * The spec is explicit that the sidebar is for navigation alone ("avoid legacy
 * sidebar widgets"), which is why the API-status and scoring-mode readouts that
 * used to sit at the bottom of it now live in the top bar.
 */
const NAV_ITEMS = [
  { name: "Home", href: "/", icon: Home },
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Upload", href: "/upload", icon: FileUp },
  { name: "Jobs", href: "/jobs", icon: Briefcase },
  { name: "Results", href: "/results", icon: BarChart3 },
  { name: "History", href: "/history", icon: History },
  { name: "Shortlist", href: "/shortlist", icon: Star },
] as const;

export function Sidebar({
  open = false,
  onNavigate,
  onClose,
}: {
  /** Only consulted below lg, where this is a drawer. */
  open?: boolean;
  /** Closes the drawer after a link is followed. */
  onNavigate?: () => void;
  onClose?: () => void;
}) {
  const pathname = usePathname();
  const isDesktop = useIsDesktop();

  /*
   * A transform moves the drawer out of sight but leaves its nine links in the
   * tab order, so on a phone the first Tab press lands in a menu nobody can
   * see. `inert` takes the whole subtree out of the tab order, out of hit
   * testing and out of the accessibility tree in one attribute.
   *
   * Deliberately driven by a media query rather than by `visibility: hidden`
   * under a `transition-[transform,visibility]`, which is the usual trick. That
   * version works, but it makes focusability a side effect of an animation
   * completing -- and an animation that does not run leaves the drawer
   * permanently unreachable. Interaction should not depend on the compositor.
   */
  const hidden = !isDesktop && !open;

  return (
    <aside
      inert={hidden}
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/10",
        "shadow-glow-lg backdrop-blur-xl transition-transform duration-300 ease-out",
        // Nearly opaque as a drawer, since it sits over the page; the
        // translucent treatment only makes sense beside content, not on top.
        "bg-surface-container-low/95 lg:bg-surface-container-low/40",
        "lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full"
      )}
    >
      <div className="flex items-start justify-between gap-3 border-b border-white/10 p-gutter">
        <Link href="/" className="block min-w-0" onClick={onNavigate}>
          <h1 className="text-headline-lg font-bold tracking-tight text-primary">
            Recruiter Pro
          </h1>
          <p className="label-sm mt-1 text-tertiary">CV Intelligence</p>
        </Link>

        {/* Only where the drawer exists. On desktop there is nothing to close,
            and a button that does nothing is the thing this project keeps
            deleting. */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close navigation"
          className="-mr-1 shrink-0 rounded p-2 text-tertiary transition-colors hover:bg-primary/10 hover:text-primary lg:hidden"
        >
          <X className="h-5 w-5" aria-hidden />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-4 py-6">
        <ul className="space-y-1">
          {NAV_ITEMS.map(({ name, href, icon: Icon }) => {
            // Exact match for "/", prefix match elsewhere, so /jobs/ENG-0001
            // keeps Jobs highlighted.
            const isActive =
              href === "/" ? pathname === "/" : pathname.startsWith(href);

            return (
              <li key={href}>
                <Link
                  href={href}
                  onClick={onNavigate}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-4 rounded px-4 py-3 transition-all duration-300 active:scale-95",
                    isActive
                      ? "border-r-4 border-primary bg-primary/10 font-bold text-primary"
                      : "font-medium text-on-surface-variant hover:bg-primary/5 hover:text-primary"
                  )}
                >
                  <Icon className="h-5 w-5 shrink-0" aria-hidden />
                  <span>{name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-gutter">
        <Link href="/upload" onClick={onNavigate} className="btn-primary w-full">
          <ScanLine className="h-5 w-5" aria-hidden />
          Analyze Resume
        </Link>
      </div>
    </aside>
  );
}
