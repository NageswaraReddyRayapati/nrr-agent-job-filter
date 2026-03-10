"""SQLAlchemy ORM models."""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


class Resume(Base):
    """Stores uploaded and parsed resumes."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    raw_text = Column(Text, nullable=True)
    parsed_profile = Column(Text, nullable=True)  # JSON string
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    skills_json = Column(Text, nullable=True)  # JSON array
    experience_summary = Column(Text, nullable=True)
    education_summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = relationship("Job", back_populates="resume")

    @property
    def skills(self) -> list:
        if self.skills_json:
            return json.loads(self.skills_json)
        return []

    @property
    def parsed_profile_dict(self) -> dict:
        if self.parsed_profile:
            return json.loads(self.parsed_profile)
        return {}


class JobPreferences(Base):
    """Stores user's job search preferences."""
    __tablename__ = "job_preferences"

    id = Column(Integer, primary_key=True, index=True)
    target_titles_json = Column(Text, default="[]")   # JSON array
    locations_json = Column(Text, default="[]")        # JSON array
    experience_level = Column(String(50), default="Mid")
    job_types_json = Column(Text, default='["Full-time"]')  # JSON array
    min_salary = Column(String(50), nullable=True)
    industries_json = Column(Text, default="[]")       # JSON array
    job_boards_json = Column(Text, default='["Google Jobs"]')  # JSON array
    excluded_companies_json = Column(Text, default="[]")  # JSON array
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def target_titles(self) -> list:
        return json.loads(self.target_titles_json or "[]")

    @property
    def locations(self) -> list:
        return json.loads(self.locations_json or "[]")

    @property
    def job_types(self) -> list:
        return json.loads(self.job_types_json or "[]")

    @property
    def industries(self) -> list:
        return json.loads(self.industries_json or "[]")

    @property
    def job_boards(self) -> list:
        return json.loads(self.job_boards_json or "[]")

    @property
    def excluded_companies(self) -> list:
        return json.loads(self.excluded_companies_json or "[]")


class Job(Base):
    """Stores found jobs and their application status."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)

    # Job details
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    apply_url = Column(String(1024), nullable=True)
    source = Column(String(100), nullable=True)  # Google Jobs, Indeed, etc.
    date_posted = Column(String(50), nullable=True)
    job_type = Column(String(50), nullable=True)
    salary_range = Column(String(100), nullable=True)

    # Scoring
    match_score = Column(Float, nullable=True)
    ats_score_before = Column(Float, nullable=True)
    ats_score_after = Column(Float, nullable=True)
    match_reasons_json = Column(Text, nullable=True)  # JSON array

    # Tailored resume
    tailored_resume_path = Column(String(512), nullable=True)
    tailored_resume_text = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default="Not Applied")  # Not Applied, Applied, Tailoring...
    date_applied = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resume = relationship("Resume", back_populates="jobs")

    @property
    def match_reasons(self) -> list:
        if self.match_reasons_json:
            return json.loads(self.match_reasons_json)
        return []


class AppSettings(Base):
    """Stores application settings including encrypted API keys."""
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
