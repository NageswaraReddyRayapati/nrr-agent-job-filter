# AI Job Search Agent

An AI-powered job search and resume tailoring agent with a full web UI. Upload your resume, set job preferences, and let AI search for matching jobs, score them, and generate tailored resumes for each position to maximize your ATS score.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│   Settings → Resume Upload → Preferences → Job Dashboard    │
│   (Vite + TypeScript + Tailwind CSS, port 3000)             │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  /api/resume  /api/preferences  /api/jobs  /api/settings    │
│  (Python 3.11+, port 8000)                                  │
│                                                             │
│  Services:                                                  │
│  ├── ResumeParser     (PDF/DOCX/TXT + LLM extraction)      │
│  ├── JobSearcher      (SerpAPI + extensible scrapers)       │
│  ├── JobMatcher       (LLM + heuristic scoring)             │
│  ├── ATSOptimizer     (keyword scoring & suggestions)       │
│  ├── ResumeTailor     (LLM-powered per-job tailoring)       │
│  ├── ResumeGenerator  (DOCX + PDF output)                   │
│  └── ApplicationMgr   (status tracking)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   SQLite Database                            │
│  resumes | job_preferences | jobs | app_settings            │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

- **Resume Upload** — PDF, DOCX, or TXT. AI-extracts name, email, phone, skills, experience.
- **Job Preferences** — Target titles, locations, experience level, job type, salary, industries, job boards.
- **Multi-Board Job Search** — SerpAPI (Google Jobs) with extensible architecture for more boards.
- **AI Matching & Scoring** — Match score (0–100) based on skill overlap, experience, location.
- **ATS Optimization** — Keyword scoring before/after tailoring.
- **Resume Tailoring** — Per-job tailored resumes generated as DOCX/PDF.
- **Application Tracking** — Track which jobs you've applied to.
- **Settings UI** — Configure OpenAI & SerpAPI keys via UI (stored encrypted) or `.env` file.

---

## Prerequisites

- **Docker & Docker Compose** (recommended)
- Or: **Python 3.11+** and **Node.js 18+** for manual setup

### API Keys
- **OpenAI API Key** — for resume parsing, job matching, and tailoring ([Get one](https://platform.openai.com/api-keys))
- **SerpAPI Key** — for Google Jobs search ([Get one](https://serpapi.com)) — *optional, mock results shown without it*

---

## Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/NageswaraReddyRayapati/nrr-agent-job-filter.git
cd nrr-agent-job-filter

# 2. Copy environment file
cp .env.example .env
# Edit .env with your API keys (or configure via UI later)

# 3. Start all services
docker-compose up --build

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
```

---

## Manual Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create data directory
mkdir -p data uploads generated_resumes

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens on http://localhost:3000
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | *(set via UI)* |
| `SERPAPI_KEY` | SerpAPI key for Google Jobs | *(set via UI)* |
| `SECRET_KEY` | Encryption key for stored API keys | `change-this-secret-key` |
| `DATABASE_URL` | SQLite database URL | `sqlite:///./data/job_agent.db` |
| `BACKEND_HOST` | Backend host | `0.0.0.0` |
| `BACKEND_PORT` | Backend port | `8000` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |
| `VITE_API_BASE_URL` | Backend URL for frontend | `http://localhost:8000` |

---

## UI Pages

### 1. Settings
Configure your OpenAI and SerpAPI keys. Keys are stored encrypted in SQLite.
Test connections with the built-in "Test" button.

### 2. Resume Upload
Drag & drop or browse to upload your resume (PDF/DOCX/TXT up to 10 MB).
After upload, see parsed profile: name, email, phone, skills, experience summary.

### 3. Job Preferences
Configure:
- Target job titles (multi-input)
- Preferred locations
- Experience level (Entry/Mid/Senior/Lead/Architect)
- Job types (Full-time, Contract, etc.)
- Industries
- Job boards to search
- Companies to exclude

### 4. Job Dashboard
The main view after setup:
- **Search Jobs** button to trigger a new search
- Summary stats: total found, applied, pending
- Jobs table with: Title, Company, Location, Match Score, ATS Score, Status, Actions
- Color-coded scores: 🔴 <40, 🟡 40–70, 🟢 >70
- Per-job actions: Apply link, Tailor Resume, Mark as Applied, Download tailored resume
- Click any job title to see description and match reasons

---

## API Documentation

FastAPI auto-generates interactive docs at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

```
POST   /api/resume/upload          Upload & parse a resume
GET    /api/resume/current         Get active resume profile
POST   /api/preferences            Save job preferences
GET    /api/preferences            Get current preferences
PUT    /api/preferences            Update preferences
POST   /api/jobs/search            Trigger job search (background)
GET    /api/jobs                   List jobs (filterable, sortable)
POST   /api/jobs/{id}/tailor       Tailor resume for a job
PUT    /api/jobs/{id}/status       Update application status
GET    /api/jobs/{id}/resume       Download tailored resume
POST   /api/settings               Save API keys
GET    /api/settings               Get settings (masked keys)
POST   /api/settings/test/openai   Test OpenAI connection
POST   /api/settings/test/serpapi  Test SerpAPI connection
GET    /health                     Health check
```

---

## Adding New Job Board Scrapers

The job search uses an abstract base class pattern. To add a new scraper:

```python
# backend/services/job_searcher.py

class IndeedJobScraper(BaseJobScraper):
    """Scraper for Indeed jobs."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search(self, query: str, location: str, num_results: int = 20) -> list[JobSearchResult]:
        # Implement your scraper here
        results = []
        # ... fetch from Indeed API or scrape ...
        return results
```

Then register it in `JobSearcher._get_scraper()`:
```python
if board == "Indeed":
    return IndeedJobScraper(self.indeed_key)
```

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests cover:
- `test_resume_parser.py` — PDF/DOCX/TXT parsing, skill extraction, email/phone detection
- `test_job_matcher.py` — Job matching and scoring logic
- `test_ats_optimizer.py` — ATS keyword scoring and analysis

---

## Project Structure

```
nrr-agent-job-filter/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings management
│   ├── models/
│   │   ├── database.py            # SQLAlchemy setup
│   │   ├── db_models.py           # ORM models
│   │   └── schemas.py             # Pydantic schemas
│   ├── services/
│   │   ├── resume_parser.py       # PDF/DOCX/TXT parsing
│   │   ├── job_searcher.py        # Multi-board job search
│   │   ├── job_matcher.py         # LLM/heuristic scoring
│   │   ├── resume_tailor.py       # Per-job resume tailoring
│   │   ├── ats_optimizer.py       # ATS keyword scoring
│   │   ├── resume_generator.py    # DOCX/PDF generation
│   │   ├── application_manager.py # Status tracking
│   │   └── settings_service.py    # Encrypted API key storage
│   ├── routers/
│   │   ├── resume.py
│   │   ├── preferences.py
│   │   ├── jobs.py
│   │   └── settings.py
│   └── tests/
│       ├── test_resume_parser.py
│       ├── test_job_matcher.py
│       └── test_ats_optimizer.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── api/client.ts
        ├── components/
        │   ├── Header.tsx
        │   ├── Dashboard.tsx
        │   ├── ResumeUpload.tsx
        │   ├── PreferencesForm.tsx
        │   ├── JobList.tsx
        │   └── SettingsPanel.tsx
        └── types/index.ts
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run tests: `cd backend && python -m pytest tests/ -v`
5. Build frontend: `cd frontend && npm run build`
6. Commit and open a Pull Request
