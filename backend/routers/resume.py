"""Resume upload and parsing endpoints."""
from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import get_settings
from models.database import get_db
from models.db_models import Resume
from models.schemas import ResumeResponse, MessageResponse
from services.resume_parser import ResumeParser
from services.settings_service import SettingsService

router = APIRouter(prefix="/api/resume", tags=["Resume"])
logger = logging.getLogger(__name__)
settings = get_settings()
settings_svc = SettingsService()
parser = ResumeParser()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and parse a resume file (PDF, DOCX, or TXT)."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: PDF, DOCX, TXT.",
        )

    # Save uploaded file
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{os.urandom(8).hex()}_{file.filename}"
    file_path = upload_dir / safe_name

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    with open(file_path, "wb") as fh:
        fh.write(contents)

    # Parse the resume
    try:
        parsed = parser.parse(str(file_path))
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        logger.error("Resume parsing failed: %s", exc)
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {exc}")

    # Try LLM-enhanced parsing if API key is available
    openai_key = settings_svc.get_openai_key(db)
    if openai_key and parsed.get("raw_text"):
        try:
            llm_data = parser.parse_with_llm(parsed["raw_text"], openai_key)
            if llm_data:
                parsed.update({k: v for k, v in llm_data.items() if v})
        except Exception as exc:
            logger.warning("LLM parsing failed, using heuristic results: %s", exc)

    # Deactivate previous resumes
    db.query(Resume).filter(Resume.is_active == True).update({"is_active": False})  # noqa: E712

    # Save to database
    resume = Resume(
        filename=file.filename or safe_name,
        file_path=str(file_path),
        file_type=suffix.lstrip("."),
        raw_text=parsed.get("raw_text", ""),
        parsed_profile=json.dumps(parsed),
        full_name=parsed.get("full_name"),
        email=parsed.get("email"),
        phone=parsed.get("phone"),
        skills_json=json.dumps(parsed.get("skills", [])),
        experience_summary=parsed.get("experience_summary"),
        education_summary=parsed.get("education_summary"),
        is_active=True,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return _to_response(resume)


@router.get("/current", response_model=ResumeResponse)
def get_current_resume(db: Session = Depends(get_db)):
    """Get the currently active resume."""
    resume = db.query(Resume).filter(Resume.is_active == True).first()  # noqa: E712
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume found")
    return _to_response(resume)


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get a specific resume by ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _to_response(resume)


@router.delete("/{resume_id}", response_model=MessageResponse)
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Delete a resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully"}


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _to_response(resume: Resume) -> ResumeResponse:
    return ResumeResponse(
        id=resume.id,
        filename=resume.filename,
        file_type=resume.file_type,
        full_name=resume.full_name,
        email=resume.email,
        phone=resume.phone,
        skills=resume.skills,
        experience_summary=resume.experience_summary,
        education_summary=resume.education_summary,
        is_active=resume.is_active,
        created_at=resume.created_at,
    )
