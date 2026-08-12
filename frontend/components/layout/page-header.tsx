"use client";

import type { ReactNode } from "react";

/**
 * The heading block every page opens with: display-scale title, one line of
 * context, and an optional actions cluster on the right.
 *
 * The old Header component took a title and subtitle and rendered the subtitle
 * *above* the title in small grey text, which no page used as intended.
 */
export function PageHeader({
  title,
  subtitle,
  meta,
  actions,
}: {
  title: string;
  subtitle?: string;
  /** A status line under the subtitle — counts, timings, provenance. */
  meta?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-gutter flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <h1 className="text-display-lg text-on-surface">{title}</h1>
        {subtitle && <p className="mt-2 text-on-surface-variant">{subtitle}</p>}
        {meta && <div className="mt-3">{meta}</div>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap gap-3">{actions}</div>}
    </div>
  );
}
