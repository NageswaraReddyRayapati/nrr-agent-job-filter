"""Resume parsing service — PDF, DOCX, TXT support with LLM-powered extraction."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parses resume files and extracts structured data."""

    SUPPORTED_TYPES = {".pdf", ".docx", ".txt"}

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def parse(self, file_path: str) -> dict:
        """Parse a resume file and return structured data."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: {suffix}")

        if suffix == ".pdf":
            raw_text = self._extract_pdf(file_path)
        elif suffix == ".docx":
            raw_text = self._extract_docx(file_path)
        else:
            raw_text = self._extract_txt(file_path)

        structured = self._extract_structured(raw_text)
        structured["raw_text"] = raw_text
        return structured

    # ──────────────────────────────────────────────────────────────
    # Extractors
    # ──────────────────────────────────────────────────────────────

    def _extract_pdf(self, file_path: str) -> str:
        try:
            import pdfplumber
            text_parts: list[str] = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as exc:
            logger.error("PDF extraction failed: %s", exc)
            raise

    def _extract_docx(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as exc:
            logger.error("DOCX extraction failed: %s", exc)
            raise

    def _extract_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    # ──────────────────────────────────────────────────────────────
    # Structured extraction (regex-based, no LLM required)
    # ──────────────────────────────────────────────────────────────

    def _extract_structured(self, text: str) -> dict:
        """Extract structured fields from raw resume text using heuristics."""
        return {
            "full_name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "skills": self._extract_skills(text),
            "experience_summary": self._extract_experience(text),
            "education_summary": self._extract_education(text),
        }

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
        return match.group() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        match = re.search(
            r"(\+?\d[\d\s\-().]{7,}\d)", text
        )
        return match.group().strip() if match else None

    def _extract_name(self, text: str) -> Optional[str]:
        """Attempt to extract candidate name from first few lines."""
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for line in lines[:5]:
            # Skip lines that look like section headers or contain special chars
            if (
                len(line.split()) >= 2
                and len(line) < 60
                and not re.search(r"[|@:\d]", line)
                and line[0].isupper()
            ):
                return line
        return None

    def _extract_skills(self, text: str) -> list[str]:
        """Extract skills from the resume text."""
        common_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker",
            "Kubernetes", "AWS", "Azure", "GCP", "Git", "CI/CD", "REST API",
            "GraphQL", "FastAPI", "Django", "Flask", "Spring Boot", "Microservices",
            "Agile", "Scrum", "Machine Learning", "TensorFlow", "PyTorch",
            "Data Analysis", "Pandas", "NumPy", "Spark", "Hadoop", "Linux",
            "C++", "C#", ".NET", "Go", "Rust", "Swift", "Kotlin",
            "HTML", "CSS", "SCSS", "Tailwind", "Vue.js", "Angular",
            "Terraform", "Ansible", "Elasticsearch", "RabbitMQ", "Kafka",
        ]
        found: list[str] = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found.append(skill)

        # Also look for a "Skills" section
        skills_section = re.search(
            r"(?:skills|technical skills|core competencies)[:\s]*(.*?)(?:\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if skills_section:
            section_text = skills_section.group(1)
            extra = re.findall(r"[A-Za-z][A-Za-z0-9.+# ]{1,30}", section_text)
            for item in extra:
                item = item.strip()
                if item and item not in found and len(item) > 2:
                    found.append(item)

        return list(dict.fromkeys(found))  # deduplicate, preserve order

    def _extract_experience(self, text: str) -> Optional[str]:
        """Extract the experience section."""
        match = re.search(
            r"(?:experience|work experience|employment)[:\s]*(.*?)(?:education|skills|certifications|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()[:2000]
        return None

    def _extract_education(self, text: str) -> Optional[str]:
        """Extract the education section."""
        match = re.search(
            r"(?:education|academic background)[:\s]*(.*?)(?:experience|skills|certifications|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()[:1000]
        return None

    # ──────────────────────────────────────────────────────────────
    # LLM-enhanced extraction (optional, uses OpenAI)
    # ──────────────────────────────────────────────────────────────

    def parse_with_llm(self, raw_text: str, openai_api_key: str) -> dict:
        """Use OpenAI to extract a richer structured profile from resume text."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)

            prompt = f"""Extract structured information from this resume text. Return ONLY valid JSON with these fields:
{{
  "full_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "skills": ["list", "of", "skills"],
  "experience_summary": "2-3 sentence summary of work experience",
  "education_summary": "education background summary",
  "years_of_experience": number_or_null,
  "current_title": "string or null",
  "certifications": ["list of certifications"]
}}

Resume text:
{raw_text[:4000]}"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1000,
            )
            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            return json.loads(content)
        except Exception as exc:
            logger.error("LLM resume parsing failed: %s", exc)
            return {}
