/**
 * The wire shapes served by src/api.py.
 *
 * These are the API's field names, not a translation of them. Where a name
 * here disagrees with the backend, the UI silently renders the wrong number —
 * which is what happened for months with the component scores: they arrived as
 * parser_score / matcher_score / scorer_score, named for the agent a reader
 * assumed produced them, and the UI labelled the skill score "ATS" and the
 * experience score "Matching" on the strength of those names.
 */

export type RemoteType = "on-site" | "hybrid" | "remote";
export type EmploymentType = "full-time" | "part-time" | "contract" | "internship";
export type SeniorityLevel =
  | "entry"
  | "mid"
  | "senior"
  | "lead"
  | "manager"
  | "executive";
/** The API's three score bands: >= 75 accepted, 50–74 review, < 50 rejected. */
export type MatchStatus = "accepted" | "review" | "rejected";

/**
 * Fields every job carries, whether it arrives from /jobs or inside a match.
 *
 * One name per concept. Four of these used to arrive twice under two names
 * (company/company_name, location/location_city, job_type/employment_type,
 * title/job_title), so every consumer wrote `a || b` and guessed which was
 * authoritative. See backlog 5.6.
 */
export interface JobFields {
  company_name: string;
  location_city: string;
  location_country: string;
  remote_type: RemoteType;
  employment_type: EmploymentType;
  seniority_level: SeniorityLevel;
  min_experience_years: number;
  max_experience_years: number;
  description?: string | null;
  required_skills?: string[];
  preferred_skills?: string[];
  posted_date?: string | null;
  category?: string | null;
  salary_range?: string | null;
}

export interface Job extends JobFields {
  job_id: string;
  title: string;
}

/** /jobs/{id} — same as Job, with the requirement lists untruncated. */
export interface JobDetail extends Job {
  education_level?: string | null;
}

export interface Match extends JobFields {
  match_id: string;
  job_id: string;
  job_title: string;

  candidate_name?: string | null;
  /** The uploaded document's name. Only a live run knows it; storage does not. */
  cv_filename?: string | null;
  /** The stored CV's UUID. Present on history rows. */
  cv_id?: string | null;

  /** The hybrid total, 0–100. What the ranking sorts on. */
  final_score: number;
  /** The weighted rule-based total: skills, title, experience, education, keywords. */
  rule_based_score: number;
  /** Required-skill coverage alone. */
  skill_score: number;
  /** Years-of-experience fit alone. */
  experience_score: number;
  /**
   * The remaining three weighted components. Optional because stored history
   * rows predate them — a match that cannot be decomposed must be detectable,
   * not silently rendered as zeroes.
   */
  title_score?: number;
  education_score?: number;
  keyword_score?: number;
  /** The model's prediction, or null when it did not run. */
  ml_score?: number | null;

  matched_skills?: string[];
  missing_skills?: string[];

  status: MatchStatus;
  explanation?: string | null;
  /**
   * Which provider wrote the explanation — "openrouter", "ollama",
   * "rule_based". Null on stored history rows, which predate the column.
   * A rule-based fallback reads exactly like model output without this.
   */
  explanation_source?: string | null;
  timestamp: string;
}

export interface MatchResponse {
  matches: Match[];
  cv_text?: string | null;
  /** Seconds, measured server-side across the whole pipeline. */
  processing_time?: number | null;
  jobs_evaluated?: number;
  /**
   * False means the ML model did not load and the scores are rule-based only.
   * Both paths produce plausible numbers, so the difference is invisible
   * unless it is stated.
   */
  ml_scoring_enabled?: boolean;
  scoring_mode?: "hybrid" | "rule_based_only";
}

export interface JobFilters {
  search?: string;
  category?: string;
  remote_type?: string;
  seniority?: string;
}

export interface JobsResponse {
  /** Rows matching the current filters — not the corpus size. */
  total: number;
  corpus_total: number;
  skip: number;
  limit: number;
  count: number;
  filters: JobFilters;
  jobs: Job[];
}

export interface JobFacets {
  categories: string[];
  remote_types: string[];
  seniority_levels: string[];
  employment_types: string[];
  total: number;
}

export interface HistoryResponse {
  matches: Match[];
  total: number;
}

export interface HealthResponse {
  status: "healthy" | "unhealthy";
  timestamp?: string;
  components?: {
    agents_loaded?: boolean;
    jobs_loaded?: number;
    ml_model_loaded?: boolean;
    database_ready?: boolean;
    /** Which provider will answer: "ollama" | "openrouter" | "rule_based". */
    explanation_provider?: string;
    llm_enabled?: boolean;
  };
}

/** The detailed single-job breakdown from /match/single. */
export interface SingleMatchResponse {
  success: boolean;
  match_id: string;
  cv_filename: string;
  job: {
    job_id: string;
    title: string;
    company: string;
    required_skills: string[];
    min_experience: number;
  };
  result: {
    score: number;
    decision: string;
    confidence: number;
    reason: string;
  };
  scores_breakdown: {
    skill_match: number;
    title_match: number;
    experience_match: number;
    education_match: number;
    keyword_match: number;
    rule_based_score: number;
    ml_score: number | null;
    hybrid_score: number;
  };
  skills: {
    matched: string[];
    missing: string[];
    extra: string[];
  };
  insights: {
    strengths: string[];
    red_flags: string[];
    recommendations: string[];
    overqualified: boolean;
    underqualified: boolean;
  };
}

/** GET /stats — the figures the landing page quotes, measured live. */
export interface Stats {
  corpus: {
    jobs: number;
    countries: number;
    cities: number;
    companies: number;
    distinct_skills: number;
    top_countries: { country: string; jobs: number }[];
  };
  engine: {
    agents: number;
    ml_model_loaded: boolean;
    model_name: string | null;
    scoring_mode: "hybrid" | "rule_based_only";
    canonical_skills: number;
    skill_aliases: number;
    explanation_provider: string;
  };
}
