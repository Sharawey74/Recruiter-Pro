import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * A timestamp, formatted identically on the server and in the browser.
 *
 * `toLocaleDateString()` with no locale uses the runtime's own — Node's on the
 * server, the user's in the browser — so the two renders disagree on any
 * machine not set to en-US and React reports a hydration mismatch. Pinning the
 * locale and the time zone makes the output a pure function of the input.
 */
const DATE_FORMAT = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

const DATE_TIME_FORMAT = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC",
  hour12: false,
});

export function formatDate(date: string | Date): string {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return "—";
  return DATE_FORMAT.format(parsed);
}

export function formatDateTime(date: string | Date): string {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return "—";
  return `${DATE_TIME_FORMAT.format(parsed)} UTC`;
}

/** "Senior Data Scientist" -> "SD". Used for candidate avatars. */
export function initials(name: string): string {
  const parts = name.trim().split(/[\s_.-]+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return parts
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join("");
}

export function titleCase(value: string): string {
  return value.replace(/\b\w/g, (character) => character.toUpperCase());
}
