"use client";

import { useState, useEffect, useCallback } from "react";
import { getJobs } from "@/lib/api";
import { toast } from "sonner";
import { Search, Loader2, Building2, MapPin, Briefcase, ChevronDown, ChevronUp } from "lucide-react";
import type { Job } from "@/lib/types";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  // Derived from the API rather than hardcoded. The header previously claimed
  // "3,000+" while the API served 4,000 out of a 6,146-record file.
  const [total, setTotal] = useState(0);
  const limit = 12;

  useEffect(() => {
    loadJobs();
  }, [page, search]);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const response = await getJobs(limit, page * limit, search);
      
      if (response.jobs.length < limit) {
        setHasMore(false);
      }

      setTotal(response.total ?? 0);
      setJobs((prev) => (page === 0 ? response.jobs : [...prev, ...response.jobs]));
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  // Debounced search
  const handleSearch = useCallback(
    (value: string) => {
      setSearch(value);
      setPage(0);
      setHasMore(true);
    },
    []
  );

  return (
    <div className="max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Job Database</h1>
        <p className="text-gray-400">
          Browse and search {total > 0 ? total.toLocaleString() : ""} job descriptions
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-navy-800 rounded-xl p-6 border border-white/10 mb-8">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs by title, company, or description..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full bg-navy-900 text-white pl-12 pr-4 py-3 rounded-lg border border-white/10 focus:outline-none focus:border-blue-500 placeholder-gray-500"
            />
          </div>
        </div>
      </div>

      {/* Job Grid */}
      {loading && page === 0 ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-navy-800 rounded-xl p-12 border border-white/10 text-center">
          <p className="text-gray-400 text-lg">No jobs found</p>
          <p className="text-gray-500 text-sm mt-2">Try adjusting your search query</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {jobs.map((job) => (
              <JobCard
                key={job.job_id}
                job={job}
                expanded={expandedJob === job.job_id}
                onToggle={() =>
                  setExpandedJob(expandedJob === job.job_id ? null : job.job_id)
                }
              />
            ))}
          </div>

          {/* Load More */}
          {hasMore && (
            <div className="mt-8 text-center">
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={loading}
                className="bg-blue-500 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-600 disabled:opacity-50 transition-all inline-flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Loading...
                  </>
                ) : (
                  "Load More"
                )}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function JobCard({
  job,
  expanded,
  onToggle,
}: {
  job: Job;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="bg-navy-800 rounded-xl p-6 border border-white/10 hover:border-blue-500/50 transition-all">
      <h3 className="text-lg font-bold text-white mb-2">{job.job_title || job.title}</h3>
      
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <Building2 className="w-4 h-4" />
          <span>{job.company}</span>
        </div>
        
        {job.location && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <MapPin className="w-4 h-4" />
            <span>{job.location}</span>
          </div>
        )}
        
        {job.job_type && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <Briefcase className="w-4 h-4" />
            <span>{job.job_type}</span>
          </div>
        )}
      </div>

      {job.description && (
        <p className="text-gray-400 text-sm line-clamp-3 mb-4">{job.description}</p>
      )}

      {/* Toggle Details */}
      <button
        onClick={onToggle}
        className="w-full text-blue-400 hover:text-blue-300 flex items-center justify-center gap-2 text-sm font-medium transition-colors"
      >
        {expanded ? (
          <>
            <ChevronUp className="w-4 h-4" />
            Show Less
          </>
        ) : (
          <>
            <ChevronDown className="w-4 h-4" />
            Show More
          </>
        )}
      </button>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-white/10 space-y-3">
          {job.description && (
            <div>
              <h4 className="text-sm font-semibold text-white mb-2">📋 Full Description</h4>
              {/* whitespace-pre-line: descriptions carry real newlines (four
                  sections and bullet lists). Without it the whole posting
                  collapses into one run-on paragraph. */}
              <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-line">{job.description}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            {job.experience_level && (
              <div>
                <p className="text-xs text-gray-500 mb-1">Experience</p>
                <p className="text-sm text-white">{job.experience_level}</p>
              </div>
            )}
            {job.salary_range && (
              <div>
                <p className="text-xs text-gray-500 mb-1">Salary</p>
                <p className="text-sm text-white">{job.salary_range}</p>
              </div>
            )}
          </div>

          <div className="text-xs text-gray-500 font-mono">Job ID: {job.job_id}</div>
        </div>
      )}
    </div>
  );
}
