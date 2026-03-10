"""Tests for the ResumeParser service."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.resume_parser import ResumeParser


@pytest.fixture
def parser():
    return ResumeParser()


@pytest.fixture
def sample_resume_txt(tmp_path):
    content = """John Doe
john.doe@example.com | +1-555-123-4567

SUMMARY
Experienced Software Engineer with 5 years of experience in Python and Java.

SKILLS
Python, Java, Docker, AWS, SQL, PostgreSQL, React, FastAPI

EXPERIENCE
Senior Software Engineer - Tech Corp (2020-2024)
- Led development of microservices using Python and FastAPI
- Managed AWS infrastructure with Terraform
- Improved system performance by 40%

EDUCATION
B.S. Computer Science - State University (2019)
"""
    file_path = tmp_path / "resume.txt"
    file_path.write_text(content)
    return str(file_path)


def test_parse_txt_extracts_email(parser, sample_resume_txt):
    result = parser.parse(sample_resume_txt)
    assert result["email"] == "john.doe@example.com"


def test_parse_txt_extracts_name(parser, sample_resume_txt):
    result = parser.parse(sample_resume_txt)
    assert result["full_name"] == "John Doe"


def test_parse_txt_extracts_skills(parser, sample_resume_txt):
    result = parser.parse(sample_resume_txt)
    skills = result["skills"]
    assert isinstance(skills, list)
    assert len(skills) > 0
    assert "Python" in skills


def test_parse_txt_extracts_raw_text(parser, sample_resume_txt):
    result = parser.parse(sample_resume_txt)
    assert "John Doe" in result["raw_text"]
    assert "Python" in result["raw_text"]


def test_parse_unsupported_type(parser, tmp_path):
    bad_file = tmp_path / "resume.xyz"
    bad_file.write_text("test")
    with pytest.raises(ValueError, match="Unsupported file type"):
        parser.parse(str(bad_file))


def test_extract_email():
    p = ResumeParser()
    assert p._extract_email("Contact: user@example.com for more info") == "user@example.com"
    assert p._extract_email("No email here") is None


def test_extract_phone():
    p = ResumeParser()
    assert p._extract_phone("+1 555 123 4567") is not None
    assert p._extract_phone("No phone here") is None


def test_extract_skills_common():
    p = ResumeParser()
    text = "I have experience with Python, JavaScript, Docker and AWS"
    skills = p._extract_skills(text)
    assert "Python" in skills
    assert "Docker" in skills
    assert "AWS" in skills


def test_parse_txt_phone(parser, sample_resume_txt):
    result = parser.parse(sample_resume_txt)
    assert result["phone"] is not None
