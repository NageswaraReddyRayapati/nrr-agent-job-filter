"""Pydantic schemas for API request/response models."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Resume schemas
# ──────────────────────────────────────────────

class ResumeBase(BaseModel):
    filename: str
    file_type: str


class ResumeProfile(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = []
    experience_summary: Optional[str] = None
    education_summary: Optional[str] = None
    parsed_profile: Optional[dict] = None


class ResumeResponse(ResumeBase):
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = []
    experience_summary: Optional[str] = None
    education_summary: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Job Preferences schemas
# ──────────────────────────────────────────────

class JobPreferencesCreate(BaseModel):
    target_titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    experience_level: str = "Mid"
    job_types: list[str] = Field(default_factory=lambda: ["Full-time"])
    min_salary: Optional[str] = None
    industries: list[str] = Field(default_factory=list)
    job_boards: list[str] = Field(default_factory=lambda: ["Google Jobs"])
    excluded_companies: list[str] = Field(default_factory=list)


class JobPreferencesResponse(JobPreferencesCreate):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Job schemas
# ──────────────────────────────────────────────

class JobBase(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    apply_url: Optional[str] = None
    source: Optional[str] = None
    date_posted: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None


class JobResponse(JobBase):
    id: int
    resume_id: Optional[int] = None
    match_score: Optional[float] = None
    ats_score_before: Optional[float] = None
    ats_score_after: Optional[float] = None
    match_reasons: list[str] = []
    tailored_resume_path: Optional[str] = None
    status: str = "Not Applied"
    date_applied: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobSearchRequest(BaseModel):
    resume_id: Optional[int] = None
    preferences_id: Optional[int] = None


class JobStatusUpdate(BaseModel):
    status: str


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    applied: int
    not_applied: int
    tailoring: int


# ──────────────────────────────────────────────
# Settings schemas
# ──────────────────────────────────────────────

class SettingsCreate(BaseModel):
    openai_api_key: Optional[str] = None
    serpapi_key: Optional[str] = None


class SettingsResponse(BaseModel):
    openai_api_key_set: bool = False
    serpapi_key_set: bool = False
    openai_api_key_masked: Optional[str] = None
    serpapi_key_masked: Optional[str] = None


# ──────────────────────────────────────────────
# Generic response
# ──────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
