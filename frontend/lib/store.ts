"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import type { Match, MatchStatus } from "./types";

/**
 * One session state, one storage key, one subscription.
 *
 * There were five independent localStorage keys — matchResults, latestAnalysis,
 * selectedFileName, candidateStatus, useLLM — written by four pages that never
 * agreed on who owned what. Clearing history in one page had to remember to
 * delete all five by hand, and a page that mounted after another had written
 * never learned about it, because localStorage fires no event in the tab that
 * wrote it.
 *
 * This is an external store, so it is read through useSyncExternalStore rather
 * than copied into component state inside an effect. That matters for more
 * than tidiness: `useState(() => localStorage…)` runs on the server too, where
 * there is no localStorage, so the server HTML and the first client render
 * disagree and React throws a hydration mismatch. useSyncExternalStore is
 * built for exactly this — it renders getServerSnapshot during hydration and
 * switches to the live snapshot immediately afterwards.
 */

const STORAGE_KEY = "recruiter-pro.session.v1";

export interface SessionState {
  /** The most recent run's matches, so Results survives a reload. */
  matches: Match[];
  /** The CV those matches came from. */
  cvFilename: string | null;
  /** Server-measured seconds for that run. */
  processingTime: number | null;
  jobsEvaluated: number | null;
  /** Whether that run used the ML model or fell back to rules. */
  scoringMode: "hybrid" | "rule_based_only" | null;
  analyzedAt: string | null;
  /** Recruiter decisions keyed by match_id, overriding the score-derived status. */
  statusOverrides: Record<string, MatchStatus>;
  /** Ask the backend for LLM explanations. Slow, and needs a provider. */
  useLLM: boolean;
  /**
   * False while this is the server snapshot. Components render skeletons
   * rather than zeroes until storage has actually been read.
   */
  hydrated: boolean;
}

export const EMPTY_SESSION: SessionState = {
  matches: [],
  cvFilename: null,
  processingTime: null,
  jobsEvaluated: null,
  scoringMode: null,
  analyzedAt: null,
  statusOverrides: {},
  useLLM: false,
  hydrated: false,
};

type Listener = () => void;

const listeners = new Set<Listener>();
let current: SessionState = EMPTY_SESSION;
let loaded = false;

function read(): SessionState {
  const base = { ...EMPTY_SESSION, hydrated: true };
  if (typeof window === "undefined") return base;

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return base;
    // Spread over the defaults: a payload written by an earlier build is
    // missing whatever fields have been added since, and reading `undefined`
    // where an array is expected crashes the page that renders it.
    return { ...base, ...(JSON.parse(raw) as Partial<SessionState>), hydrated: true };
  } catch {
    return base;
  }
}

/**
 * Must return a referentially stable value between writes, or
 * useSyncExternalStore re-renders forever. `current` is only ever reassigned
 * in write().
 */
function getSnapshot(): SessionState {
  if (!loaded) {
    current = read();
    loaded = true;
  }
  return current;
}

/** During SSR and hydration. Nothing is known about the browser yet. */
function getServerSnapshot(): SessionState {
  return EMPTY_SESSION;
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);

  // Another tab wrote. Re-read rather than trusting event.newValue, which is
  // null when storage was cleared.
  const onStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY || event.key === null) {
      current = read();
      listeners.forEach((notify) => notify());
    }
  };
  window.addEventListener("storage", onStorage);

  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

function write(state: SessionState) {
  current = state;
  loaded = true;

  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Quota exceeded or storage disabled. The in-memory state is still
      // correct for this tab; only persistence is lost.
    }
  }
  listeners.forEach((notify) => notify());
}

export function updateSession(patch: Partial<SessionState>) {
  write({ ...getSnapshot(), ...patch, hydrated: true });
}

export function clearSession() {
  write({ ...EMPTY_SESSION, hydrated: true });
}

/**
 * Records a completed run. Called in one place, so nothing can persist matches
 * while forgetting the provenance that goes with them.
 */
export function recordAnalysis(args: {
  matches: Match[];
  cvFilename: string;
  processingTime?: number | null;
  jobsEvaluated?: number | null;
  scoringMode?: "hybrid" | "rule_based_only" | null;
}) {
  updateSession({
    matches: args.matches,
    cvFilename: args.cvFilename,
    processingTime: args.processingTime ?? null,
    jobsEvaluated: args.jobsEvaluated ?? null,
    scoringMode: args.scoringMode ?? null,
    analyzedAt: new Date().toISOString(),
  });
}

export function setMatchStatus(matchId: string, status: MatchStatus) {
  updateSession({
    statusOverrides: { ...getSnapshot().statusOverrides, [matchId]: status },
  });
}

export function useSession() {
  const state = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const effectiveStatus = useCallback(
    (match: Match): MatchStatus => state.statusOverrides[match.match_id] ?? match.status,
    [state.statusOverrides]
  );

  return useMemo(
    () => ({
      ...state,
      effectiveStatus,
      update: updateSession,
      clear: clearSession,
      record: recordAnalysis,
      setStatus: setMatchStatus,
    }),
    [state, effectiveStatus]
  );
}
