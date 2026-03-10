import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, RefreshCw, ExternalLink, Download, CheckCircle,
  Loader2, ChevronUp, ChevronDown, Filter
} from 'lucide-react';
import toast from 'react-hot-toast';
import { listJobs, triggerSearch, tailorResume, updateJobStatus, getTailoredResumeUrl } from '../api/client';
import type { Job, JobListResponse } from '../types';

interface JobListProps {
  onSearchComplete?: () => void;
}

const ScoreBadge: React.FC<{ score?: number | null; label?: string }> = ({ score, label }) => {
  if (score == null) return <span className="text-gray-400 text-xs">N/A</span>;
  const color =
    score >= 70 ? 'bg-green-100 text-green-700' :
    score >= 40 ? 'bg-yellow-100 text-yellow-700' :
    'bg-red-100 text-red-700';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      {label ? `${label}: ` : ''}{score}
    </span>
  );
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const color =
    status === 'Applied' ? 'bg-green-100 text-green-700' :
    status === 'Tailoring...' ? 'bg-purple-100 text-purple-700' :
    status === 'Interviewing' ? 'bg-blue-100 text-blue-700' :
    status === 'Rejected' ? 'bg-red-100 text-red-700' :
    status === 'Offer' ? 'bg-yellow-100 text-yellow-700' :
    'bg-gray-100 text-gray-600';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {status}
    </span>
  );
};

const JobList: React.FC<JobListProps> = ({ onSearchComplete }) => {
  const [jobData, setJobData] = useState<JobListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [sortBy, setSortBy] = useState('match_score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);

  const fetchJobs = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await listJobs({
        status: filterStatus || undefined,
        sort_by: sortBy,
        order: sortOrder,
      });
      setJobData(data);
      // Stop polling if no tailoring jobs
      const hasTailoring = data.jobs.some(j => j.status === 'Tailoring...');
      if (!hasTailoring && pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    } catch (err) {
      // Silently fail on polling
    } finally {
      setIsLoading(false);
    }
  }, [filterStatus, sortBy, sortOrder, pollingInterval]);

  useEffect(() => {
    fetchJobs();
  }, [filterStatus, sortBy, sortOrder]);

  const handleSearch = async () => {
    setIsSearching(true);
    try {
      const result = await triggerSearch();
      toast.success(result.message);
      // Poll for results
      const interval = window.setInterval(fetchJobs, 3000);
      setPollingInterval(interval);
      setTimeout(() => {
        clearInterval(interval);
        setPollingInterval(null);
        fetchJobs();
        onSearchComplete?.();
      }, 60000); // Stop polling after 1 minute
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to start search');
    } finally {
      setIsSearching(false);
    }
  };

  const handleTailor = async (jobId: number) => {
    try {
      await tailorResume(jobId);
      toast.success('Resume tailoring started...');
      // Poll for completion
      const interval = window.setInterval(fetchJobs, 2000);
      setTimeout(() => {
        clearInterval(interval);
        fetchJobs();
      }, 30000);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Tailoring failed');
    }
  };

  const handleMarkApplied = async (jobId: number) => {
    try {
      await updateJobStatus(jobId, 'Applied');
      toast.success('Marked as applied!');
      fetchJobs();
    } catch (err: any) {
      toast.error('Failed to update status');
    }
  };

  const toggleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const SortIcon: React.FC<{ column: string }> = ({ column }) => {
    if (sortBy !== column) return null;
    return sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Job Dashboard</h2>
          {jobData && (
            <p className="text-gray-500 text-sm mt-0.5">
              {jobData.total} jobs found · {jobData.applied} applied · {jobData.not_applied} pending
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchJobs}
            disabled={isLoading}
            className="flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
          >
            {isSearching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            {isSearching ? 'Searching...' : 'Search Jobs'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {jobData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Total Found', value: jobData.total, color: 'blue' },
            { label: 'Applied', value: jobData.applied, color: 'green' },
            { label: 'Pending', value: jobData.not_applied, color: 'yellow' },
            { label: 'Tailoring', value: jobData.tailoring, color: 'purple' },
          ].map(card => (
            <div key={card.label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm text-center">
              <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{card.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 bg-white rounded-xl border border-gray-200 p-3 shadow-sm">
        <Filter size={14} className="text-gray-400" />
        <span className="text-sm text-gray-500">Filter:</span>
        {['', 'Not Applied', 'Applied', 'Tailoring...'].map(status => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors
              ${filterStatus === status ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {status || 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {isLoading && !jobData ? (
          <div className="p-12 text-center">
            <Loader2 className="animate-spin mx-auto text-blue-500" size={32} />
            <p className="text-gray-500 mt-2">Loading jobs...</p>
          </div>
        ) : !jobData || jobData.jobs.length === 0 ? (
          <div className="p-12 text-center">
            <Search className="mx-auto text-gray-300" size={40} />
            <p className="text-gray-500 mt-2 font-medium">No jobs found yet</p>
            <p className="text-gray-400 text-sm mt-1">Click "Search Jobs" to find matching positions</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  {[
                    { key: 'title', label: 'Job Title' },
                    { key: 'company', label: 'Company' },
                    { key: 'location', label: 'Location' },
                    { key: 'match_score', label: 'Match' },
                    { key: 'ats_score_before', label: 'ATS' },
                    { key: 'status', label: 'Status' },
                    { key: 'actions', label: 'Actions', noSort: true },
                  ].map(col => (
                    <th
                      key={col.key}
                      className={`px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide
                        ${!col.noSort ? 'cursor-pointer hover:text-gray-900 select-none' : ''}`}
                      onClick={() => !col.noSort && toggleSort(col.key)}
                    >
                      <div className="flex items-center gap-1">
                        {col.label}
                        {!col.noSort && <SortIcon column={col.key} />}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {jobData.jobs.map((job, idx) => (
                  <tr
                    key={job.id}
                    className={`border-b border-gray-100 hover:bg-gray-50 transition-colors
                      ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                  >
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedJob(selectedJob?.id === job.id ? null : job)}
                        className="font-medium text-blue-600 hover:underline text-left"
                      >
                        {job.title}
                      </button>
                      {job.source && <p className="text-xs text-gray-400">{job.source}</p>}
                    </td>
                    <td className="px-4 py-3 text-gray-700">{job.company || '-'}</td>
                    <td className="px-4 py-3 text-gray-600">{job.location || '-'}</td>
                    <td className="px-4 py-3"><ScoreBadge score={job.match_score} /></td>
                    <td className="px-4 py-3">
                      {job.ats_score_after != null ? (
                        <div className="flex flex-col gap-0.5">
                          <ScoreBadge score={job.ats_score_before} label="Before" />
                          <ScoreBadge score={job.ats_score_after} label="After" />
                        </div>
                      ) : (
                        <ScoreBadge score={job.ats_score_before} />
                      )}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={job.status} /></td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {job.apply_url && (
                          <a
                            href={job.apply_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs hover:bg-blue-100"
                          >
                            <ExternalLink size={10} />Apply
                          </a>
                        )}
                        {job.status !== 'Tailoring...' && !job.tailored_resume_path && (
                          <button
                            onClick={() => handleTailor(job.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-600 rounded text-xs hover:bg-purple-100"
                          >
                            <Loader2 size={10} />Tailor
                          </button>
                        )}
                        {job.tailored_resume_path && (
                          <a
                            href={getTailoredResumeUrl(job.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-600 rounded text-xs hover:bg-green-100"
                          >
                            <Download size={10} />Resume
                          </a>
                        )}
                        {job.status !== 'Applied' && (
                          <button
                            onClick={() => handleMarkApplied(job.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-gray-50 text-gray-600 rounded text-xs hover:bg-gray-100"
                          >
                            <CheckCircle size={10} />Applied
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Job Detail Panel */}
      {selectedJob && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{selectedJob.title}</h3>
              <p className="text-gray-500">
                {selectedJob.company} · {selectedJob.location}
                {selectedJob.salary_range && ` · ${selectedJob.salary_range}`}
              </p>
            </div>
            <button onClick={() => setSelectedJob(null)} className="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          {selectedJob.match_reasons.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-1">Match Reasons</p>
              <ul className="text-sm text-gray-600 space-y-0.5">
                {selectedJob.match_reasons.map((r, i) => (
                  <li key={i} className="flex items-center gap-1">
                    <span className="text-green-500">✓</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {selectedJob.description && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-1">Description</p>
              <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
                {selectedJob.description}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default JobList;
