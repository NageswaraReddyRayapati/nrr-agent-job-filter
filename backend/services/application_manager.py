"""Application manager service — tracks application status and manages job list."""
from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from models.db_models import Job

logger = logging.getLogger(__name__)


class ApplicationManager:
    """Manages job application status and tracking."""

    def update_status(self, db: Session, job_id: int, status: str) -> Job | None:
        """Update the application status of a job."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        valid_statuses = {"Not Applied", "Applied", "Tailoring...", "Interviewing", "Rejected", "Offer"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        job.status = status
        if status == "Applied" and not job.date_applied:
            job.date_applied = datetime.utcnow()
        job.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(job)
        logger.info("Updated job %d status to '%s'", job_id, status)
        return job

    def get_summary(self, db: Session) -> dict:
        """Get application summary statistics."""
        jobs = db.query(Job).all()
        total = len(jobs)
        applied = sum(1 for j in jobs if j.status == "Applied")
        not_applied = sum(1 for j in jobs if j.status == "Not Applied")
        tailoring = sum(1 for j in jobs if j.status == "Tailoring...")

        return {
            "total": total,
            "applied": applied,
            "not_applied": not_applied,
            "tailoring": tailoring,
        }
