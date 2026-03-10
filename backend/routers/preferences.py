"""Job preferences CRUD endpoints."""
from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.db_models import JobPreferences
from models.schemas import JobPreferencesCreate, JobPreferencesResponse

router = APIRouter(prefix="/api/preferences", tags=["Preferences"])
logger = logging.getLogger(__name__)


@router.post("", response_model=JobPreferencesResponse)
def create_preferences(
    body: JobPreferencesCreate,
    db: Session = Depends(get_db),
):
    """Save job search preferences."""
    # Deactivate old preferences
    db.query(JobPreferences).filter(JobPreferences.is_active == True).update(  # noqa: E712
        {"is_active": False}
    )
    prefs = JobPreferences(
        target_titles_json=json.dumps(body.target_titles),
        locations_json=json.dumps(body.locations),
        experience_level=body.experience_level,
        job_types_json=json.dumps(body.job_types),
        min_salary=body.min_salary,
        industries_json=json.dumps(body.industries),
        job_boards_json=json.dumps(body.job_boards),
        excluded_companies_json=json.dumps(body.excluded_companies),
        is_active=True,
    )
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return _to_response(prefs)


@router.get("", response_model=JobPreferencesResponse)
def get_preferences(db: Session = Depends(get_db)):
    """Get current active preferences."""
    prefs = db.query(JobPreferences).filter(JobPreferences.is_active == True).first()  # noqa: E712
    if not prefs:
        raise HTTPException(status_code=404, detail="No preferences found")
    return _to_response(prefs)


@router.put("/{pref_id}", response_model=JobPreferencesResponse)
def update_preferences(
    pref_id: int,
    body: JobPreferencesCreate,
    db: Session = Depends(get_db),
):
    """Update existing preferences."""
    prefs = db.query(JobPreferences).filter(JobPreferences.id == pref_id).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")

    prefs.target_titles_json = json.dumps(body.target_titles)
    prefs.locations_json = json.dumps(body.locations)
    prefs.experience_level = body.experience_level
    prefs.job_types_json = json.dumps(body.job_types)
    prefs.min_salary = body.min_salary
    prefs.industries_json = json.dumps(body.industries)
    prefs.job_boards_json = json.dumps(body.job_boards)
    prefs.excluded_companies_json = json.dumps(body.excluded_companies)
    prefs.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(prefs)
    return _to_response(prefs)


@router.put("", response_model=JobPreferencesResponse)
def upsert_preferences(
    body: JobPreferencesCreate,
    db: Session = Depends(get_db),
):
    """Create or update preferences (upsert)."""
    prefs = db.query(JobPreferences).filter(JobPreferences.is_active == True).first()  # noqa: E712
    if prefs:
        return update_preferences(prefs.id, body, db)
    return create_preferences(body, db)


# ──────────────────────────────────────────────────────────────

def _to_response(prefs: JobPreferences) -> JobPreferencesResponse:
    return JobPreferencesResponse(
        id=prefs.id,
        target_titles=prefs.target_titles,
        locations=prefs.locations,
        experience_level=prefs.experience_level,
        job_types=prefs.job_types,
        min_salary=prefs.min_salary,
        industries=prefs.industries,
        job_boards=prefs.job_boards,
        excluded_companies=prefs.excluded_companies,
        is_active=prefs.is_active,
        created_at=prefs.created_at,
        updated_at=prefs.updated_at,
    )
