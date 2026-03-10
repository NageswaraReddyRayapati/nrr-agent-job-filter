"""Tests for the ATSOptimizer service."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ats_optimizer import ATSOptimizer


@pytest.fixture
def optimizer():
    return ATSOptimizer()


SAMPLE_RESUME = """
John Doe
john@example.com

SUMMARY
Experienced Python developer with expertise in FastAPI and AWS.

SKILLS
Python, FastAPI, Docker, PostgreSQL, AWS, Git, CI/CD

EXPERIENCE
Software Engineer - Tech Corp (2021-2024)
- Developed REST APIs using Python FastAPI
- Deployed services to AWS using Docker containers
- Reduced deployment time by 35% through CI/CD improvements

EDUCATION
B.S. Computer Science - State University (2021)
"""

SAMPLE_JOB = """
We are looking for a Python Backend Engineer with experience in:
- Python (FastAPI or Django)
- PostgreSQL database management
- Docker and Kubernetes
- AWS or GCP cloud platforms
- RESTful API design
- Agile methodologies
- CI/CD pipelines
The ideal candidate has 3+ years of experience and strong communication skills.
"""


def test_score_returns_dict(optimizer):
    result = optimizer.score(SAMPLE_RESUME, SAMPLE_JOB)
    assert isinstance(result, dict)
    assert "score" in result
    assert "matched_keywords" in result
    assert "missing_keywords" in result
    assert "suggestions" in result


def test_score_range(optimizer):
    result = optimizer.score(SAMPLE_RESUME, SAMPLE_JOB)
    assert 0 <= result["score"] <= 100


def test_matched_keywords_are_subset(optimizer):
    result = optimizer.score(SAMPLE_RESUME, SAMPLE_JOB)
    resume_lower = SAMPLE_RESUME.lower()
    for kw in result["matched_keywords"]:
        assert kw in resume_lower


def test_missing_keywords(optimizer):
    result = optimizer.score(SAMPLE_RESUME, SAMPLE_JOB)
    # Missing keywords should be in job keywords but not in resume keyword list
    job_keywords = optimizer._extract_keywords(SAMPLE_JOB)
    resume_keywords = set(optimizer._extract_keywords(SAMPLE_RESUME))
    for kw in result["missing_keywords"]:
        assert kw in job_keywords
        assert kw not in resume_keywords


def test_good_resume_scores_higher_than_empty(optimizer):
    empty_score = optimizer.score("", SAMPLE_JOB)
    good_score = optimizer.score(SAMPLE_RESUME, SAMPLE_JOB)
    assert good_score["score"] >= empty_score["score"]


def test_get_missing_keywords(optimizer):
    missing = optimizer.get_missing_keywords(SAMPLE_RESUME, SAMPLE_JOB)
    assert isinstance(missing, list)
    resume_keywords = set(optimizer._extract_keywords(SAMPLE_RESUME))
    for kw in missing:
        # Each missing keyword should NOT be in the resume keyword set
        assert kw not in resume_keywords


def test_suggestions_list(optimizer):
    result = optimizer.score(SAMPLE_RESUME, SAMPLE_JOB)
    assert isinstance(result["suggestions"], list)


def test_score_with_matching_resume(optimizer):
    """A resume with all job keywords should score high."""
    matching_resume = SAMPLE_JOB  # Use job desc as resume
    result = optimizer.score(matching_resume, SAMPLE_JOB)
    assert result["score"] >= 80
