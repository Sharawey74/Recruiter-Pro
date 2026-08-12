"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileUp,
  Briefcase,
  BarChart3,
  History,
  Star,
  ScanLine,
} from "lucide-react";
import { cn } from "@/lib/utils";

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
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Upload", href: "/upload", icon: FileUp },
  { name: "Jobs", href: "/jobs", icon: Briefcase },
  { name: "Results", href: "/results", icon: BarChart3 },
  { name: "History", href: "/history", icon: History },
  { name: "Shortlist", href: "/shortlist", icon: Star },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/10 bg-surface-container-low/40 shadow-glow-lg backdrop-blur-xl">
      <div className="border-b border-white/10 p-gutter">
        <Link href="/" className="block">
          <h1 className="text-headline-lg font-bold tracking-tight text-primary">
            Recruiter Pro
          </h1>
          <p className="label-sm mt-1 text-tertiary">CV Intelligence</p>
        </Link>
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
        <Link href="/upload" className="btn-primary w-full">
          <ScanLine className="h-5 w-5" aria-hidden />
          Analyze Resume
        </Link>
      </div>
    </aside>
  );
}
