import axios from "axios";
import type {
  MatchResponse,
  SingleMatchResponse,
  JobsResponse,
  JobDetail,
  JobFacets,
  JobFilters,
  HistoryResponse,
  HealthResponse,
  Stats,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  // A full match against the 800-job corpus runs in well under a second now
  // that scoring is batched, so the old 150s ceiling only meant a hung request
  // held the UI for two and a half minutes before reporting anything.
  timeout: 60000,
});

/**
 * Whatever axios threw, as a sentence worth showing a user.
 *
 * Every page had its own `error.response?.data?.detail || "Failed to ..."`,
 * which renders "Network Error" as a generic failure message and loses the
 * distinction between "the API is down" and "the API said no".
 */
export function apiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail) return detail;
    if (error.code === "ECONNABORTED") return "The request timed out.";
    if (!error.response) {
      return `Cannot reach the API at ${API_BASE}. Is the backend running?`;
    }
    return `${fallback} (HTTP ${error.response.status})`;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export async function getStats(): Promise<Stats> {
  const { data } = await api.get("/stats");
  return data;
}

export async function checkHealth(): Promise<HealthResponse> {
  const { data } = await api.get("/health");
  return data;
}

export async function getJobs(
  limit = 12,
  skip = 0,
  filters: JobFilters = {}
): Promise<JobsResponse> {
  const { data } = await api.get("/jobs", {
    params: {
      limit,
      skip,
      // Empty strings are dropped rather than sent: `?search=` would be a
      // filter for the empty string, which matches every row by accident.
      search: filters.search || undefined,
      category: filters.category || undefined,
      remote_type: filters.remote_type || undefined,
      seniority: filters.seniority || undefined,
    },
  });
  return data;
}

export async function getJobFacets(): Promise<JobFacets> {
  const { data } = await api.get("/jobs/facets");
  return data;
}

export async function getJob(jobId: string): Promise<JobDetail> {
  const { data } = await api.get(`/jobs/${encodeURIComponent(jobId)}`);
  return data;
}

export async function matchCV(
  file: File,
  topK = 10,
  useLLM = false
): Promise<MatchResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post("/match", formData, {
    // Params as params. Building the query string by hand meant a filename
    // was never the problem but any future string value would be unescaped.
    params: {
      top_k: topK,
      explain: useLLM,
      use_llm: useLLM,
    },
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function matchSingleJob(
  file: File,
  jobId: string,
  explain = false
): Promise<SingleMatchResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post("/match/single", formData, {
    params: { job_id: jobId, explain },
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getMatchHistory(
  limit = 50,
  skip = 0
): Promise<HistoryResponse> {
  const { data } = await api.get("/match/history", { params: { limit, skip } });
  return data;
}

export async function clearMatchHistory(): Promise<{
  success: boolean;
  deleted_count: number;
  message: string;
}> {
  const { data } = await api.delete("/match/history");
  return data;
}

export { API_BASE };
export default api;
