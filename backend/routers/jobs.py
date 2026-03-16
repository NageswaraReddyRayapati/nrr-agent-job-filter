"""Job search, list, scoring and tailoring endpoints."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models.database import get_db
from models.db_models import Job, JobPreferences, Resume
from models.schemas import (
    JobListResponse,
    JobResponse,
    JobSearchRequest,
    JobStatusUpdate,
    MessageResponse,
)
from services.application_manager import ApplicationManager
from services.ats_optimizer import ATSOptimizer
from services.job_matcher import JobMatcher
from services.job_searcher import JobSearcher
from services.resume_generator import ResumeGenerator
from services.resume_tailor import ResumeTailor
from services.settings_service import SettingsService
from config import get_settings

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])
logger = logging.getLogger(__name__)
settings = get_settings()

settings_svc = SettingsService()
app_mgr = ApplicationManager()
ats_optimizer = ATSOptimizer()


# ──────────────────────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────────────────────

@router.post("/search", response_model=MessageResponse)
def trigger_search(
    body: JobSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger a job search (runs in background). Returns immediately."""
    resume = _get_active_resume(db, body.resume_id)
    prefs = _get_active_prefs(db, body.preferences_id)

    openai_key = settings_svc.get_openai_key(db)
    serpapi_key = settings_svc.get_serpapi_key(db)

    background_tasks.add_task(
        _run_search,
        resume_id=resume.id,
        prefs_id=prefs.id,
        openai_key=openai_key,
        serpapi_key=serpapi_key,
    )
    return {"message": "Job search started in background. Refresh the job list shortly."}


# ──────────────────────────────────────────────────────────────
# List
# ──────────────────────────────────────────────────────────────

@router.get("", response_model=JobListResponse)
def list_jobs(
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    sort_by: str = "match_score",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    """List all found jobs with optional filters and sorting."""
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    if min_score is not None:
        query = query.filter(Job.match_score >= min_score)
    if max_score is not None:
        query = query.filter(Job.match_score <= max_score)

    # Sorting
    sort_col = getattr(Job, sort_by, Job.match_score)
    if order.lower() == "asc":
        query = query.order_by(sort_col.asc().nulls_last())
    else:
        query = query.order_by(sort_col.desc().nulls_last())

    jobs = query.all()
    summary = app_mgr.get_summary(db)

    return JobListResponse(
        jobs=[_to_response(j) for j in jobs],
        total=summary["total"],
        applied=summary["applied"],
        not_applied=summary["not_applied"],
        tailoring=summary["tailoring"],
    )


# ──────────────────────────────────────────────────────────────
# Single job
# ──────────────────────────────────────────────────────────────

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_response(job)


# ──────────────────────────────────────────────────────────────
# Tailor
# ──────────────────────────────────────────────────────────────

@router.post("/{job_id}/tailor", response_model=JobResponse)
def tailor_resume_for_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Tailor the resume for a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume = db.query(Resume).filter(Resume.is_active == True).first()  # noqa: E712
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume found")

    # Mark as tailoring
    job.status = "Tailoring..."
    db.commit()

    openai_key = settings_svc.get_openai_key(db)

    background_tasks.add_task(
        _run_tailor,
        job_id=job.id,
        resume_id=resume.id,
        openai_key=openai_key,
    )
    return _to_response(job)


# ──────────────────────────────────────────────────────────────
# Status update
# ──────────────────────────────────────────────────────────────

@router.put("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: int,
    body: JobStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the application status of a job."""
    job = app_mgr.update_status(db, job_id, body.status)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_response(job)


# ──────────────────────────────────────────────────────────────
# Download tailored resume
# ──────────────────────────────────────────────────────────────

@router.get("/{job_id}/resume")
def download_tailored_resume(job_id: int, db: Session = Depends(get_db)):
    """Download the tailored resume for a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.tailored_resume_path or not os.path.exists(job.tailored_resume_path):
        raise HTTPException(status_code=404, detail="Tailored resume not yet generated")
    return FileResponse(
        path=job.tailored_resume_path,
        filename=os.path.basename(job.tailored_resume_path),
        media_type="application/octet-stream",
    )


# ──────────────────────────────────────────────────────────────
# Background tasks
# ──────────────────────────────────────────────────────────────

def _run_search(
    resume_id: int,
    prefs_id: int,
    openai_key: str,
    serpapi_key: str,
):
    """Background task: search for jobs and score them."""
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        prefs = db.query(JobPreferences).filter(JobPreferences.id == prefs_id).first()
        if not resume or not prefs:
            logger.error("Resume or preferences not found for search task")
            return

        searcher = JobSearcher(serpapi_key=serpapi_key, request_delay=settings.job_search_delay)
        matcher = JobMatcher(openai_api_key=openai_key, llm_delay=settings.llm_request_delay)

        results = searcher.search(
            titles=prefs.target_titles or ["Software Engineer"],
            locations=prefs.locations or ["Remote"],
            boards=prefs.job_boards or ["Google Jobs"],
            skills=resume.skills,
        )

        logger.info("Found %d jobs, scoring...", len(results))
        excluded = {c.lower() for c in prefs.excluded_companies}

        for result in results:
            # Skip excluded companies
            if result.company and result.company.lower() in excluded:
                continue

            score_data = matcher.score(
                job_title=result.title,
                job_description=result.description,
                job_location=result.location,
                resume_skills=resume.skills,
                experience_summary=resume.experience_summary or "",
                preferred_titles=prefs.target_titles,
                preferred_locations=prefs.locations,
            )

            ats_data = ats_optimizer.score(resume.raw_text or "", result.description)

            job = Job(
                resume_id=resume.id,
                title=result.title,
                company=result.company,
                location=result.location,
                description=result.description,
                apply_url=result.apply_url,
                source=result.source,
                date_posted=result.date_posted,
                job_type=result.job_type,
                salary_range=result.salary_range,
                match_score=score_data.get("score", 0),
                ats_score_before=ats_data.get("score", 0),
                match_reasons_json=json.dumps(score_data.get("reasons", [])),
                status="Not Applied",
            )
            db.add(job)

        db.commit()
        logger.info("Job search complete. %d jobs saved.", len(results))
    except Exception as exc:
        logger.error("Background search failed: %s", exc)
        db.rollback()
    finally:
        db.close()


def _run_tailor(job_id: int, resume_id: int, openai_key: str):
    """Background task: tailor resume for a specific job."""
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not job or not resume:
            logger.error("Job or resume not found for tailoring task")
            return

        resume_text = resume.raw_text or ""
        job_desc = job.description or ""

        missing_kws = ats_optimizer.get_missing_keywords(resume_text, job_desc)

        tailor = ResumeTailor(openai_api_key=openai_key, llm_delay=settings.llm_request_delay)
        result = tailor.tailor(
            resume_text=resume_text,
            job_title=job.title,
            job_description=job_desc,
            company=job.company or "",
            missing_keywords=missing_kws,
        )

        tailored_text = result.get("tailored_text", resume_text)

        # Generate files
        gen = ResumeGenerator(output_dir=settings.generated_resumes_dir)
        safe_prefix = f"job_{job_id}_resume"
        try:
            file_path = gen.generate_docx(tailored_text, safe_prefix)
        except Exception as exc:
            logger.warning("DOCX generation failed, trying PDF: %s", exc)
            file_path = gen.generate_pdf(tailored_text, safe_prefix)

        # ATS score after tailoring
        ats_after = ats_optimizer.score(tailored_text, job_desc)

        job.tailored_resume_path = file_path
        job.tailored_resume_text = tailored_text
        job.ats_score_after = ats_after.get("score", 0)
        job.status = "Not Applied"
        job.updated_at = datetime.utcnow()
        db.commit()
        logger.info("Tailoring complete for job %d, file: %s", job_id, file_path)
    except Exception as exc:
        logger.error("Background tailoring failed for job %d: %s", job_id, exc)
        db.rollback()
        # Reset status on failure
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "Not Applied"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _get_active_resume(db: Session, resume_id: Optional[int] = None) -> Resume:
    if resume_id:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
    else:
        resume = db.query(Resume).filter(Resume.is_active == True).first()  # noqa: E712
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume found. Please upload a resume first.")
    return resume


def _get_active_prefs(db: Session, prefs_id: Optional[int] = None) -> JobPreferences:
    if prefs_id:
        prefs = db.query(JobPreferences).filter(JobPreferences.id == prefs_id).first()
    else:
        prefs = db.query(JobPreferences).filter(JobPreferences.is_active == True).first()  # noqa: E712
    if not prefs:
        raise HTTPException(
            status_code=404, detail="No job preferences found. Please set up preferences first."
        )
    return prefs


def _to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        resume_id=job.resume_id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        apply_url=job.apply_url,
        source=job.source,
        date_posted=job.date_posted,
        job_type=job.job_type,
        salary_range=job.salary_range,
        match_score=job.match_score,
        ats_score_before=job.ats_score_before,
        ats_score_after=job.ats_score_after,
        match_reasons=job.match_reasons,
        tailored_resume_path=job.tailored_resume_path,
        status=job.status,
        date_applied=job.date_applied,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
