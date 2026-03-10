"""Job search service using SerpAPI (Google Jobs) with extensible scraper architecture."""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class JobSearchResult:
    """Represents a single job search result."""

    def __init__(
        self,
        title: str,
        company: str,
        location: str,
        description: str,
        apply_url: str,
        source: str,
        date_posted: Optional[str] = None,
        job_type: Optional[str] = None,
        salary_range: Optional[str] = None,
    ):
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.apply_url = apply_url
        self.source = source
        self.date_posted = date_posted
        self.job_type = job_type
        self.salary_range = salary_range

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "apply_url": self.apply_url,
            "source": self.source,
            "date_posted": self.date_posted,
            "job_type": self.job_type,
            "salary_range": self.salary_range,
        }


# ──────────────────────────────────────────────────────────────
# Abstract base class — add new scrapers by subclassing this
# ──────────────────────────────────────────────────────────────

class BaseJobScraper(ABC):
    """Abstract base class for job board scrapers."""

    @abstractmethod
    def search(
        self,
        query: str,
        location: str,
        num_results: int = 20,
    ) -> list[JobSearchResult]:
        """Search for jobs matching query in location."""

    def _safe_str(self, value, default: str = "") -> str:
        if value is None:
            return default
        return str(value)


# ──────────────────────────────────────────────────────────────
# SerpAPI (Google Jobs) scraper
# ──────────────────────────────────────────────────────────────

class SerpAPIJobScraper(BaseJobScraper):
    """Job scraper using SerpAPI Google Jobs engine."""

    def __init__(self, api_key: str, request_delay: float = 1.0):
        self.api_key = api_key
        self.request_delay = request_delay

    def search(
        self,
        query: str,
        location: str,
        num_results: int = 20,
    ) -> list[JobSearchResult]:
        try:
            from serpapi import GoogleSearch
        except ImportError:
            logger.error("serpapi package not installed")
            return []

        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "num": num_results,
            "api_key": self.api_key,
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            jobs_results = results.get("jobs_results", [])
        except Exception as exc:
            logger.error("SerpAPI search failed: %s", exc)
            return []

        time.sleep(self.request_delay)
        return [self._parse_result(job) for job in jobs_results]

    def _parse_result(self, job: dict) -> JobSearchResult:
        # Extract apply URL from extensions or detected extensions
        apply_url = ""
        extensions = job.get("detected_extensions", {})
        related_links = job.get("related_links", [])
        if related_links:
            apply_url = related_links[0].get("link", "")

        description = job.get("description", "")
        highlights = job.get("job_highlights", [])
        if highlights:
            for h in highlights:
                items = h.get("items", [])
                description += "\n" + "\n".join(items)

        return JobSearchResult(
            title=self._safe_str(job.get("title")),
            company=self._safe_str(job.get("company_name")),
            location=self._safe_str(job.get("location")),
            description=description,
            apply_url=apply_url,
            source="Google Jobs",
            date_posted=self._safe_str(extensions.get("posted_at")),
            job_type=self._safe_str(extensions.get("schedule_type")),
            salary_range=self._safe_str(extensions.get("salary")),
        )


# ──────────────────────────────────────────────────────────────
# Mock scraper (used when no API key is configured)
# ──────────────────────────────────────────────────────────────

class MockJobScraper(BaseJobScraper):
    """Returns sample jobs for testing when no API key is available."""

    def search(
        self,
        query: str,
        location: str,
        num_results: int = 20,
    ) -> list[JobSearchResult]:
        logger.warning("Using mock job scraper — configure SerpAPI key for real results")
        sample_jobs = [
            {
                "title": f"{query} - Sample Position 1",
                "company": "Tech Corp",
                "location": location or "Remote",
                "description": f"We are looking for a {query} with strong technical skills. "
                               "Requirements: 3+ years experience, proficiency in relevant technologies, "
                               "good communication skills. Responsibilities include design, development, "
                               "and maintenance of software systems.",
                "apply_url": "https://example.com/apply/1",
                "date_posted": "2 days ago",
                "job_type": "Full-time",
                "salary_range": "$80,000 - $120,000",
            },
            {
                "title": f"Senior {query}",
                "company": "Startup Inc",
                "location": location or "Remote",
                "description": f"Join our growing team as a Senior {query}. "
                               "You will lead technical initiatives and mentor junior engineers. "
                               "5+ years of experience required. Experience with cloud platforms preferred.",
                "apply_url": "https://example.com/apply/2",
                "date_posted": "1 week ago",
                "job_type": "Full-time",
                "salary_range": "$120,000 - $160,000",
            },
            {
                "title": f"Lead {query}",
                "company": "Enterprise Solutions Ltd",
                "location": location or "Hybrid",
                "description": f"We are seeking a Lead {query} to drive our engineering strategy. "
                               "Responsibilities: architectural design, team leadership, cross-functional collaboration. "
                               "8+ years of experience required.",
                "apply_url": "https://example.com/apply/3",
                "date_posted": "3 days ago",
                "job_type": "Full-time",
                "salary_range": "$150,000 - $200,000",
            },
        ]
        results = []
        for job in sample_jobs[:num_results]:
            results.append(
                JobSearchResult(
                    title=job["title"],
                    company=job["company"],
                    location=job["location"],
                    description=job["description"],
                    apply_url=job["apply_url"],
                    source="Mock (no API key)",
                    date_posted=job["date_posted"],
                    job_type=job["job_type"],
                    salary_range=job["salary_range"],
                )
            )
        return results


# ──────────────────────────────────────────────────────────────
# Job Searcher — orchestrates multiple scrapers
# ──────────────────────────────────────────────────────────────

class JobSearcher:
    """Orchestrates job search across multiple scrapers."""

    def __init__(self, serpapi_key: str = "", request_delay: float = 1.0):
        self.serpapi_key = serpapi_key
        self.request_delay = request_delay

    def _get_scraper(self, board: str) -> Optional[BaseJobScraper]:
        if board in ("Google Jobs", "SerpAPI"):
            if self.serpapi_key:
                return SerpAPIJobScraper(self.serpapi_key, self.request_delay)
            return MockJobScraper()
        # Future scrapers: Indeed, LinkedIn, JobStreet, etc.
        logger.warning("No scraper available for board: %s, using mock", board)
        return MockJobScraper()

    def search(
        self,
        titles: list[str],
        locations: list[str],
        boards: list[str],
        skills: list[str] | None = None,
        num_results_per_query: int = 10,
    ) -> list[JobSearchResult]:
        """Search for jobs matching titles + locations across specified boards."""
        all_results: list[JobSearchResult] = []
        seen_urls: set[str] = set()

        if not locations:
            locations = ["Remote"]
        if not boards:
            boards = ["Google Jobs"]

        for board in boards:
            scraper = self._get_scraper(board)
            if not scraper:
                continue
            for title in titles:
                for location in locations:
                    query = title
                    if skills:
                        query = f"{title} {' '.join(skills[:3])}"
                    logger.info("Searching '%s' in '%s' on %s", query, location, board)
                    try:
                        results = scraper.search(query, location, num_results_per_query)
                        for result in results:
                            if result.apply_url not in seen_urls:
                                seen_urls.add(result.apply_url)
                                all_results.append(result)
                        time.sleep(self.request_delay)
                    except Exception as exc:
                        logger.error("Search error for %s/%s: %s", title, location, exc)

        return all_results
