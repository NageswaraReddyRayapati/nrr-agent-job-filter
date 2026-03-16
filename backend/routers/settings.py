"""Settings / API key management endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import SettingsCreate, SettingsResponse, MessageResponse
from services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["Settings"])
logger = logging.getLogger(__name__)
settings_svc = SettingsService()


@router.post("", response_model=SettingsResponse)
def save_settings(body: SettingsCreate, db: Session = Depends(get_db)):
    """Save API keys (stored encrypted in the database)."""
    settings_svc.save(db, body.openai_api_key, body.serpapi_key)
    return settings_svc.get(db)


@router.get("", response_model=SettingsResponse)
def get_settings_endpoint(db: Session = Depends(get_db)):
    """Get current settings (API keys are masked)."""
    return settings_svc.get(db)


@router.post("/test/openai", response_model=MessageResponse)
def test_openai(db: Session = Depends(get_db)):
    """Test the OpenAI API key connection."""
    key = settings_svc.get_openai_key(db)
    if not key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        client.models.list()
        return {"message": "OpenAI connection successful!"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OpenAI connection failed: {exc}")


@router.post("/test/serpapi", response_model=MessageResponse)
def test_serpapi(db: Session = Depends(get_db)):
    """Test the SerpAPI key connection."""
    key = settings_svc.get_serpapi_key(db)
    if not key:
        raise HTTPException(status_code=400, detail="SerpAPI key not configured")
    try:
        from serpapi import GoogleSearch
        params = {"engine": "google", "q": "test", "api_key": key, "num": 1}
        search = GoogleSearch(params)
        result = search.get_dict()
        if "error" in result:
            raise ValueError(result["error"])
        return {"message": "SerpAPI connection successful!"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"SerpAPI connection failed: {exc}")
