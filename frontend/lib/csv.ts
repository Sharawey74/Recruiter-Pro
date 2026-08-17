"use client";

import type { Match, MatchStatus } from "./types";

/**
 * Exporting matches as CSV, because recruiters work in spreadsheets.
 *
 * This began as a local function inside the Results page. It moved here when
 * Shortlist and History needed it too — the shortlist in particular, since a
 * shortlist is the thing a recruiter actually hands to somebody else.
 *
 * Generated in the browser rather than served from an endpoint: the rows are
 * already in memory on every page that offers the button, so a round trip would
 * fetch data the page is currently rendering.
 */

/**
 * One field, escaped.
 *
 * Quoted only when it has to be — a comma, a quote or a newline — and embedded
 * quotes doubled. The previous version quoted every field unconditionally,
 * which is valid CSV and makes the file noisier to read in a text editor.
 *
 * The newline case is the one that matters. Explanations are free prose from a
 * language model: they routinely contain commas, they can contain quotation
 * marks, and nothing stops one containing a line break. Mishandled, a single
 * explanation shifts every later column on that row and the file opens
 * misaligned rather than broken, which is worse because nobody notices.
 */
function field(value: unknown): string {
  if (value === null || value === undefined) return "";

  const text = String(value);
  if (!/[",\n\r]/.test(text)) return text;
  return `"${text.replace(/"/g, '""')}"`;
}

export function toCsv(headers: string[], rows: unknown[][]): string {
  const lines = [headers, ...rows].map((row) => row.map(field).join(","));
  // CRLF and a trailing newline: RFC 4180 specifies it, and Excel on Windows is
  // the likeliest destination.
  return lines.join("\r\n") + "\r\n";
}

/**
 * The columns, in one place.
 *
 * Every score component gets its own column rather than only the total.
 * Reporting the parts is what this product does differently, and an export that
 * collapsed them to one number would be the one place it stopped.
 */
const COLUMNS: [string, (m: Match, status: MatchStatus) => unknown][] = [
  ["candidate", (m) => m.candidate_name ?? ""],
  ["job_id", (m) => m.job_id],
  ["job_title", (m) => m.job_title],
  ["company", (m) => m.company_name ?? ""],
  ["location", (m) => [m.location_city, m.location_country].filter(Boolean).join(", ")],
  ["remote_type", (m) => m.remote_type],
  ["seniority", (m) => m.seniority_level],
  ["salary_range", (m) => m.salary_range ?? ""],
  ["final_score", (m) => m.final_score],
  ["rule_based_score", (m) => m.rule_based_score],
  ["skill_score", (m) => m.skill_score],
  ["experience_score", (m) => m.experience_score],
  // Empty, not zero. The model did not score zero; it did not run.
  ["ml_score", (m) => m.ml_score ?? ""],
  ["status", (_m, status) => status],
  ["matched_skills", (m) => (m.matched_skills ?? []).join("; ")],
  ["missing_skills", (m) => (m.missing_skills ?? []).join("; ")],
  ["explanation", (m) => m.explanation ?? ""],
  // Without this column a rule-based sentence and a model-written one are
  // indistinguishable once they leave the app, which is exactly the confusion
  // `explanation_source` exists to prevent.
  ["explanation_source", (m) => m.explanation_source ?? ""],
  ["analysed_at", (m) => m.timestamp],
];

export function matchesToCsv(
  matches: Match[],
  effectiveStatus: (match: Match) => MatchStatus
): string {
  return toCsv(
    COLUMNS.map(([header]) => header),
    matches.map((match) => COLUMNS.map(([, read]) => read(match, effectiveStatus(match))))
  );
}

/** `recruiter-pro-shortlist-2026-08-17.csv` */
export function csvFilename(label: string): string {
  const slug = label.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9-]+/g, "-") || "export";
  return `recruiter-pro-${slug}-${new Date().toISOString().slice(0, 10)}.csv`;
}

/**
 * Hand the file to the browser.
 *
 * The leading U+FEFF is for Excel: without a byte-order mark it reads the file
 * as the system code page and mangles any non-ASCII name — and candidate names
 * are exactly where non-ASCII shows up.
 */
export function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}
