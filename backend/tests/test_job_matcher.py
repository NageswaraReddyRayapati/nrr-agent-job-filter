"""Tests for the JobMatcher service."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.job_matcher import JobMatcher


@pytest.fixture
def matcher():
    # No API key = heuristic mode
    return JobMatcher(openai_api_key="")


def test_score_perfect_title_match(matcher):
    result = matcher.score(
        job_title="Senior Python Developer",
        job_description="We need a Senior Python Developer with FastAPI and Docker experience.",
        job_location="Remote",
        resume_skills=["Python", "FastAPI", "Docker", "AWS"],
        experience_summary="5 years of Python development",
        preferred_titles=["Senior Python Developer"],
        preferred_locations=["Remote"],
    )
    assert result["score"] > 50
    assert "score" in result
    assert "reasons" in result
    assert isinstance(result["reasons"], list)


def test_score_no_match(matcher):
    result = matcher.score(
        job_title="Marketing Manager",
        job_description="Looking for experienced marketing professional with social media skills.",
        job_location="New York",
        resume_skills=["Python", "Java", "AWS"],
        experience_summary="Software engineer background",
        preferred_titles=["Software Engineer"],
        preferred_locations=["Remote"],
    )
    assert result["score"] < 50


def test_score_returns_dict(matcher):
    result = matcher.score(
        job_title="Data Engineer",
        job_description="Data engineering role with Spark and Python",
        job_location="Singapore",
        resume_skills=["Python", "Spark"],
        experience_summary="Data pipeline experience",
        preferred_titles=["Data Engineer"],
        preferred_locations=["Singapore"],
    )
    assert isinstance(result, dict)
    assert "score" in result
    assert 0 <= result["score"] <= 100


def test_score_skill_match(matcher):
    result = matcher.score(
        job_title="Backend Engineer",
        job_description=(
            "We need someone with Python, FastAPI, PostgreSQL, Docker, AWS, Redis."
        ),
        job_location="Remote",
        resume_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis"],
        experience_summary="Backend developer",
        preferred_titles=["Backend Engineer"],
        preferred_locations=["Remote"],
    )
    # All skills match => high score
    assert result["score"] >= 40


def test_score_location_match(matcher):
    result = matcher.score(
        job_title="Engineer",
        job_description="Software engineering role",
        job_location="Remote",
        resume_skills=["Python"],
        experience_summary="",
        preferred_titles=["Engineer"],
        preferred_locations=["Remote"],
    )
    assert result["score"] > 0
