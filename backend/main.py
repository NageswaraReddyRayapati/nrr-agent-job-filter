"""FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_settings
from models.database import init_db
from routers import jobs, preferences, resume, settings as settings_router

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# App lifecycle
# ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("Starting AI Job Search Agent backend...")
    init_db()

    # Create required directories
    cfg = get_settings()
    os.makedirs(cfg.upload_dir, exist_ok=True)
    os.makedirs(cfg.generated_resumes_dir, exist_ok=True)
    logger.info("Database initialized. Directories created.")
    yield
    logger.info("Shutting down...")


# ──────────────────────────────────────────────────────────────
# App instance
# ──────────────────────────────────────────────────────────────

cfg = get_settings()

app = FastAPI(
    title=cfg.app_name,
    version=cfg.app_version,
    description=(
        "AI-powered Job Search & Application Agent. "
        "Upload your resume, set preferences, and let AI find and tailor jobs for you."
    ),
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────

app.include_router(resume.router)
app.include_router(preferences.router)
app.include_router(jobs.router)
app.include_router(settings_router.router)


# ──────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": cfg.app_version}


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "AI Job Search Agent API",
        "docs": "/docs",
        "version": cfg.app_version,
    }
