"""ATS (Applicant Tracking System) keyword scoring service."""
from __future__ import annotations

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Common ATS-important section headers
SECTION_HEADERS = {
    "summary", "objective", "experience", "education", "skills",
    "certifications", "projects", "awards", "languages", "publications",
}

# Words that are typically filtered by ATS
ATS_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can",
}


class ATSOptimizer:
    """Scores and optimizes resumes for ATS keyword matching."""

    def score(self, resume_text: str, job_description: str) -> dict:
        """
        Compute an ATS match score between resume text and job description.

        Returns a dict with:
          - score (0-100)
          - matched_keywords: list of keywords found in both
          - missing_keywords: important job keywords not in resume
          - suggestions: list of improvement suggestions
        """
        job_keywords = self._extract_keywords(job_description)
        resume_keywords = self._extract_keywords(resume_text)

        matched = [kw for kw in job_keywords if kw in resume_keywords]
        missing = [kw for kw in job_keywords if kw not in resume_keywords]

        # Weighted score: frequency of keyword coverage
        score = 0
        if job_keywords:
            score = int(len(matched) / len(job_keywords) * 100)

        # Bonus for section headers present
        section_bonus = self._section_header_score(resume_text)
        score = min(score + section_bonus, 100)

        suggestions = self._generate_suggestions(missing, resume_text)

        return {
            "score": score,
            "matched_keywords": matched[:20],
            "missing_keywords": missing[:20],
            "suggestions": suggestions,
            "total_job_keywords": len(job_keywords),
            "matched_count": len(matched),
        }

    def get_missing_keywords(self, resume_text: str, job_description: str) -> list[str]:
        """Get keywords from job description missing in resume."""
        job_keywords = self._extract_keywords(job_description)
        resume_keywords = self._extract_keywords(resume_text)
        return [kw for kw in job_keywords if kw not in resume_keywords]

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text."""
        # Tokenize: split on whitespace and punctuation
        words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9#+.\-]{1,30}\b", text.lower())
        # Filter stopwords and short words
        words = [w for w in words if w not in ATS_STOPWORDS and len(w) > 2]

        # Get top keywords by frequency
        freq = Counter(words)
        return [word for word, _ in freq.most_common(50)]

    def _section_header_score(self, resume_text: str) -> int:
        """Bonus points for having standard resume sections."""
        text_lower = resume_text.lower()
        found = sum(1 for header in SECTION_HEADERS if header in text_lower)
        return min(found * 2, 10)

    def _generate_suggestions(self, missing_keywords: list[str], resume_text: str) -> list[str]:
        """Generate actionable suggestions for improving the resume."""
        suggestions: list[str] = []

        if missing_keywords:
            top_missing = missing_keywords[:5]
            suggestions.append(
                f"Add these keywords from the job description: {', '.join(top_missing)}"
            )

        text_lower = resume_text.lower()
        if "summary" not in text_lower and "objective" not in text_lower:
            suggestions.append("Add a professional summary/objective section at the top")

        if len(resume_text) < 300:
            suggestions.append("Resume appears too short — add more detail to experience sections")

        if "quantif" not in text_lower and "%" not in resume_text and "$" not in resume_text:
            suggestions.append(
                "Quantify achievements with numbers (e.g., 'reduced costs by 20%')"
            )

        return suggestions
