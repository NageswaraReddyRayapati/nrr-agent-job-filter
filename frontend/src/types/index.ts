// TypeScript type definitions for the AI Job Search Agent

export interface Resume {
  id: number;
  filename: string;
  file_type: string;
  full_name?: string;
  email?: string;
  phone?: string;
  skills: string[];
  experience_summary?: string;
  education_summary?: string;
  is_active: boolean;
  created_at: string;
}

export interface JobPreferences {
  id: number;
  target_titles: string[];
  locations: string[];
  experience_level: string;
  job_types: string[];
  min_salary?: string;
  industries: string[];
  job_boards: string[];
  excluded_companies: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobPreferencesCreate {
  target_titles: string[];
  locations: string[];
  experience_level: string;
  job_types: string[];
  min_salary?: string;
  industries: string[];
  job_boards: string[];
  excluded_companies: string[];
}

export type JobStatus = 'Not Applied' | 'Applied' | 'Tailoring...' | 'Interviewing' | 'Rejected' | 'Offer';

export interface Job {
  id: number;
  resume_id?: number;
  title: string;
  company?: string;
  location?: string;
  description?: string;
  apply_url?: string;
  source?: string;
  date_posted?: string;
  job_type?: string;
  salary_range?: string;
  match_score?: number;
  ats_score_before?: number;
  ats_score_after?: number;
  match_reasons: string[];
  tailored_resume_path?: string;
  status: JobStatus;
  date_applied?: string;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  applied: number;
  not_applied: number;
  tailoring: number;
}

export interface AppSettings {
  openai_api_key_set: boolean;
  serpapi_key_set: boolean;
  openai_api_key_masked?: string;
  serpapi_key_masked?: string;
}

export interface MessageResponse {
  message: string;
  detail?: string;
}

export type SetupStep = 'settings' | 'resume' | 'preferences' | 'dashboard';
