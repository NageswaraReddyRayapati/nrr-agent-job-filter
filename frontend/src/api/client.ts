import axios from 'axios';
import type {
  Resume,
  JobPreferences,
  JobPreferencesCreate,
  Job,
  JobListResponse,
  AppSettings,
  MessageResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Resume ──────────────────────────────────────────────────

export const uploadResume = async (file: File): Promise<Resume> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<Resume>('/api/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getCurrentResume = async (): Promise<Resume> => {
  const { data } = await api.get<Resume>('/api/resume/current');
  return data;
};

export const getResume = async (id: number): Promise<Resume> => {
  const { data } = await api.get<Resume>(`/api/resume/${id}`);
  return data;
};

// ── Preferences ─────────────────────────────────────────────

export const savePreferences = async (prefs: JobPreferencesCreate): Promise<JobPreferences> => {
  const { data } = await api.put<JobPreferences>('/api/preferences', prefs);
  return data;
};

export const getPreferences = async (): Promise<JobPreferences> => {
  const { data } = await api.get<JobPreferences>('/api/preferences');
  return data;
};

// ── Jobs ─────────────────────────────────────────────────────

export const triggerSearch = async (
  resumeId?: number,
  preferencesId?: number
): Promise<MessageResponse> => {
  const { data } = await api.post<MessageResponse>('/api/jobs/search', {
    resume_id: resumeId,
    preferences_id: preferencesId,
  });
  return data;
};

export const listJobs = async (params?: {
  status?: string;
  min_score?: number;
  max_score?: number;
  sort_by?: string;
  order?: string;
}): Promise<JobListResponse> => {
  const { data } = await api.get<JobListResponse>('/api/jobs', { params });
  return data;
};

export const getJob = async (id: number): Promise<Job> => {
  const { data } = await api.get<Job>(`/api/jobs/${id}`);
  return data;
};

export const tailorResume = async (jobId: number): Promise<Job> => {
  const { data } = await api.post<Job>(`/api/jobs/${jobId}/tailor`);
  return data;
};

export const updateJobStatus = async (jobId: number, status: string): Promise<Job> => {
  const { data } = await api.put<Job>(`/api/jobs/${jobId}/status`, { status });
  return data;
};

export const getTailoredResumeUrl = (jobId: number): string => {
  return `${BASE_URL}/api/jobs/${jobId}/resume`;
};

// ── Settings ─────────────────────────────────────────────────

export const saveSettings = async (settings: {
  openai_api_key?: string;
  serpapi_key?: string;
}): Promise<AppSettings> => {
  const { data } = await api.post<AppSettings>('/api/settings', settings);
  return data;
};

export const getSettings = async (): Promise<AppSettings> => {
  const { data } = await api.get<AppSettings>('/api/settings');
  return data;
};

export const testOpenAI = async (): Promise<MessageResponse> => {
  const { data } = await api.post<MessageResponse>('/api/settings/test/openai');
  return data;
};

export const testSerpAPI = async (): Promise<MessageResponse> => {
  const { data } = await api.post<MessageResponse>('/api/settings/test/serpapi');
  return data;
};

export default api;
