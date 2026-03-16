"""Job matching service — scores jobs against a candidate's resume."""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)


class JobMatcher:
    """Scores jobs by relevance to a candidate's resume profile."""

    def __init__(self, openai_api_key: str = "", llm_delay: float = 0.5):
        self.openai_api_key = openai_api_key
        self.llm_delay = llm_delay

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def score(
        self,
        job_title: str,
        job_description: str,
        job_location: str,
        resume_skills: list[str],
        experience_summary: str,
        preferred_titles: list[str],
        preferred_locations: list[str],
    ) -> dict:
        """Return a score (0-100) and reasons for a job match."""
        if self.openai_api_key:
            try:
                result = self._score_with_llm(
                    job_title,
                    job_description,
                    resume_skills,
                    experience_summary,
                    preferred_titles,
                    preferred_locations,
                )
                if result:
                    return result
            except Exception as exc:
                logger.warning("LLM scoring failed, falling back to heuristic: %s", exc)

        return self._score_heuristic(
            job_title,
            job_description,
            job_location,
            resume_skills,
            experience_summary,
            preferred_titles,
            preferred_locations,
        )

    # ──────────────────────────────────────────────────────────────
    # LLM-based scoring
    # ──────────────────────────────────────────────────────────────

    def _score_with_llm(
        self,
        job_title: str,
        job_description: str,
        resume_skills: list[str],
        experience_summary: str,
        preferred_titles: list[str],
        preferred_locations: list[str],
    ) -> Optional[dict]:
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_api_key)

        prompt = f"""Rate how well this job matches the candidate profile. Return ONLY valid JSON.

Job Title: {job_title}
Job Description (excerpt): {job_description[:1500]}

Candidate Skills: {', '.join(resume_skills[:30])}
Candidate Experience: {(experience_summary or '')[:500]}
Preferred Titles: {', '.join(preferred_titles)}

Return JSON:
{{
  "score": <integer 0-100>,
  "reasons": ["reason1", "reason2", "reason3"],
  "skill_match_percent": <integer 0-100>,
  "experience_match": "good|partial|poor"
}}"""

        time.sleep(self.llm_delay)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)

    # ──────────────────────────────────────────────────────────────
    # Heuristic scoring (fallback, no LLM required)
    # ──────────────────────────────────────────────────────────────

    def _score_heuristic(
        self,
        job_title: str,
        job_description: str,
        job_location: str,
        resume_skills: list[str],
        experience_summary: str,
        preferred_titles: list[str],
        preferred_locations: list[str],
    ) -> dict:
        score = 0
        reasons: list[str] = []
        desc_lower = job_description.lower()
        jt_lower = job_title.lower()

        # Title match (0-30 points)
        title_score = 0
        for preferred in preferred_titles:
            words = preferred.lower().split()
            if all(w in jt_lower for w in words):
                title_score = 30
                reasons.append(f"Job title matches '{preferred}'")
                break
            elif any(w in jt_lower for w in words):
                title_score = max(title_score, 15)
                reasons.append(f"Job title partially matches '{preferred}'")
        score += title_score

        # Skill match (0-50 points)
        matched_skills: list[str] = []
        for skill in resume_skills[:20]:
            if skill.lower() in desc_lower:
                matched_skills.append(skill)
        skill_ratio = len(matched_skills) / max(len(resume_skills[:20]), 1)
        skill_score = int(skill_ratio * 50)
        score += skill_score
        if matched_skills:
            reasons.append(f"Matched skills: {', '.join(matched_skills[:5])}")

        # Location match (0-20 points)
        loc_score = 0
        if not preferred_locations or "remote" in (job_location or "").lower():
            loc_score = 20
            reasons.append("Location is remote or flexible")
        else:
            for loc in preferred_locations:
                if loc.lower() in (job_location or "").lower():
                    loc_score = 20
                    reasons.append(f"Location matches '{loc}'")
                    break

        score += loc_score

        return {
            "score": min(score, 100),
            "reasons": reasons,
            "skill_match_percent": int(skill_ratio * 100),
            "experience_match": "good" if score >= 60 else "partial" if score >= 30 else "poor",
        }
