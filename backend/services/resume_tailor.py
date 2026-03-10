"""Resume tailoring service — uses LLM to customize resumes for specific jobs."""
from __future__ import annotations

import json
import logging
import re
import time

logger = logging.getLogger(__name__)


class ResumeTailor:
    """Tailors a resume to a specific job description using OpenAI."""

    def __init__(self, openai_api_key: str = "", llm_delay: float = 0.5):
        self.openai_api_key = openai_api_key
        self.llm_delay = llm_delay

    def tailor(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        company: str = "",
        missing_keywords: list[str] | None = None,
    ) -> dict:
        """
        Tailor resume text to a specific job.

        Returns:
            dict with keys: tailored_text, changes_made, keywords_added
        """
        if not self.openai_api_key:
            return self._basic_tailor(resume_text, job_title, missing_keywords or [])

        try:
            return self._tailor_with_llm(
                resume_text, job_title, job_description, company, missing_keywords or []
            )
        except Exception as exc:
            logger.error("LLM tailoring failed: %s", exc)
            return self._basic_tailor(resume_text, job_title, missing_keywords or [])

    # ──────────────────────────────────────────────────────────────
    # LLM-based tailoring
    # ──────────────────────────────────────────────────────────────

    def _tailor_with_llm(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        company: str,
        missing_keywords: list[str],
    ) -> dict:
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_api_key)

        kw_instruction = ""
        if missing_keywords:
            kw_instruction = (
                f"\nNaturally incorporate these missing keywords where relevant "
                f"(do NOT fabricate experience): {', '.join(missing_keywords[:15])}"
            )

        prompt = f"""You are an expert resume writer and ATS optimization specialist.
Tailor the following resume for the job position: {job_title} at {company or 'the company'}.

Job Description (excerpt):
{job_description[:2000]}
{kw_instruction}

Original Resume:
{resume_text[:3000]}

Instructions:
1. Rewrite the professional summary/objective to align with this job
2. Emphasize relevant skills and experience
3. Add missing keywords naturally (without fabricating experience)
4. Keep the overall structure and content truthful
5. Optimize for ATS parsers

Return ONLY valid JSON:
{{
  "tailored_text": "the full tailored resume text",
  "changes_made": ["list of key changes made"],
  "keywords_added": ["list of keywords incorporated"]
}}"""

        time.sleep(self.llm_delay)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000,
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)

    # ──────────────────────────────────────────────────────────────
    # Basic tailoring (no LLM — keyword insertion only)
    # ──────────────────────────────────────────────────────────────

    def _basic_tailor(
        self, resume_text: str, job_title: str, missing_keywords: list[str]
    ) -> dict:
        """Simple tailoring: update summary line and append missing skills."""
        tailored = resume_text

        # Replace/update objective line
        summary_pattern = re.compile(
            r"(objective|summary)[:\s]*.*?(\n\n|\n(?=[A-Z]))",
            re.IGNORECASE | re.DOTALL,
        )
        new_summary = (
            f"Objective: Seeking a {job_title} position where I can apply my skills "
            "and experience to contribute to the organization's success.\n\n"
        )
        if summary_pattern.search(tailored):
            tailored = summary_pattern.sub(new_summary, tailored, count=1)
        else:
            tailored = new_summary + tailored

        # Append missing keywords to skills section
        keywords_added: list[str] = []
        if missing_keywords:
            skills_pattern = re.compile(r"(skills[:\s]*)(.*?)(\n\n|\Z)", re.IGNORECASE | re.DOTALL)
            match = skills_pattern.search(tailored)
            if match:
                existing_skills = match.group(2)
                additions = [kw for kw in missing_keywords[:5] if kw.lower() not in existing_skills.lower()]
                if additions:
                    new_skills = existing_skills.rstrip() + ", " + ", ".join(additions)
                    tailored = tailored[: match.start(2)] + new_skills + tailored[match.end(2):]
                    keywords_added = additions

        return {
            "tailored_text": tailored,
            "changes_made": [
                f"Updated objective to target {job_title}",
                "Added missing keywords to skills section",
            ],
            "keywords_added": keywords_added,
        }
