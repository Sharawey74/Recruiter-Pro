"use client";

import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Loading and empty states.
 *
 * Every list in this app used to render a centred spinner while loading and a
 * bare "No matches found" when empty. A spinner says only "wait"; a skeleton
 * says what is coming and how much of it, so the layout does not jump when the
 * data lands. An empty state that names the next action is the difference
 * between a dead end and a step in a workflow.
 */

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("animate-pulse rounded bg-white/5", className)}
      aria-hidden
    />
  );
}

/** A card-shaped placeholder matching the match/job card grid. */
export function CardSkeleton({ delayMs = 0 }: { delayMs?: number }) {
  return (
    <div
      className="gradient-border-card p-6"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <div className="mb-6 flex items-center gap-4">
        <Skeleton className="h-12 w-12 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <div className="mb-6 space-y-3">
        <Skeleton className="h-2 w-full" />
        <Skeleton className="h-2 w-5/6" />
        <Skeleton className="h-2 w-4/6" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
    </div>
  );
}

export function CardSkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3"
      role="status"
      aria-label="Loading"
    >
      {Array.from({ length: count }, (_, index) => (
        <CardSkeleton key={index} delayMs={index * 120} />
      ))}
    </div>
  );
}

export function RowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }, (_, index) => (
        <td key={index} className="px-6 py-4">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  body,
  action,
}: {
  icon: LucideIcon;
  title: string;
  body: string;
  /** Where to go next. Omitted only when there genuinely is no next step. */
  action?: { label: string; href: string };
}) {
  return (
    <div className="glass-panel flex flex-col items-center rounded-lg px-6 py-16 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
        <Icon className="h-7 w-7 text-primary" aria-hidden />
      </div>
      <h3 className="mb-2 text-headline-md text-on-surface">{title}</h3>
      <p className="max-w-md text-on-surface-variant">{body}</p>
      {action && (
        <Link href={action.href} className="btn-secondary mt-6">
          {action.label}
        </Link>
      )}
    </div>
  );
}

/**
 * A failed fetch, with the reason and a way to try again. The pages used to
 * fire a toast and then render their empty state, so a network failure was
 * indistinguishable from having no data once the toast faded.
 */
export function ErrorState({
  icon: Icon,
  title,
  message,
  onRetry,
}: {
  icon: LucideIcon;
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      className="flex flex-col items-center rounded-lg border border-error/30 bg-error-container/20 px-6 py-16 text-center"
      role="alert"
    >
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-error/10">
        <Icon className="h-7 w-7 text-error" aria-hidden />
      </div>
      <h3 className="mb-2 text-headline-md text-on-surface">{title}</h3>
      <p className="max-w-md text-on-surface-variant">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-secondary mt-6">
          Try again
        </button>
      )}
    </div>
  );
}
