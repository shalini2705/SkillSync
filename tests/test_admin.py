"""
Unit tests for Administrator Course CRUD and authorization functions.
"""

import tempfile
import os
import pytest
from database.seed_data import seed_database
from modules.admin_dashboard import add_course, update_course, delete_course, get_admin_metrics
from database.db import fetch_one


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_admin_add_course_success(temp_db):
    """Tests creating a valid new course as an administrator."""
    ok, msg = add_course(
        course_code="AI999",
        title="Generative AI & LLM Systems",
        description="Comprehensive guide to fine-tuning transformers, prompt engineering, and RAG architectures.",
        category="Artificial Intelligence",
        difficulty="Advanced",
        duration=32,
        skills=["Machine Learning", "Python"],
        target_roles=["Machine Learning Engineer"],
        prereq_codes=["ML201"],
        db_path=temp_db
    )
    assert ok is True
    assert "successfully added" in msg.lower()

    # Query the newly added course
    created = fetch_one("SELECT * FROM courses WHERE course_code = 'AI999'", db_path=temp_db)
    assert created is not None
    assert created["title"] == "Generative AI & LLM Systems"
    assert created["estimated_duration_hours"] == 32


def test_admin_duplicate_course_code_rejected(temp_db):
    """Ensures duplicate course codes are rejected."""
    ok, err = add_course(
        course_code="PY101",  # Existing seed code
        title="Duplicate Python",
        description="This should be rejected due to non-unique code.",
        category="Programming",
        difficulty="Beginner",
        duration=10,
        skills=["Python"],
        target_roles=["Python Developer"],
        db_path=temp_db
    )
    assert ok is False
    assert "already exists" in err.lower()


def test_admin_update_course(temp_db):
    """Tests updating an existing course's metadata and duration."""
    course = fetch_one("SELECT id FROM courses WHERE course_code = 'PY101'", db_path=temp_db)
    cid = course["id"]

    ok, msg = update_course(
        course_id=cid,
        title="Mastering Python 3 & Design Patterns",
        description="Advanced object-oriented programming, design patterns, and clean architecture.",
        category="Programming",
        difficulty="Intermediate",
        duration=35,
        skills=["Python", "Git"],
        target_roles=["Python Developer", "Software Engineer"],
        db_path=temp_db
    )
    assert ok is True

    updated = fetch_one("SELECT * FROM courses WHERE id = ?", (cid,), db_path=temp_db)
    assert updated["title"] == "Mastering Python 3 & Design Patterns"
    assert updated["difficulty_level"] == "Intermediate"
    assert updated["estimated_duration_hours"] == 35


def test_admin_delete_course(temp_db):
    """Tests deleting a course from the catalog."""
    # First add a throwaway course
    add_course(
        course_code="TEMP101",
        title="Temporary Course",
        description="This course is created specifically for testing deletion.",
        category="Testing",
        difficulty="Beginner",
        duration=5,
        skills=["Git"],
        target_roles=["Software Engineer"],
        db_path=temp_db
    )
    course = fetch_one("SELECT id FROM courses WHERE course_code = 'TEMP101'", db_path=temp_db)
    assert course is not None
    cid = course["id"]

    ok, msg = delete_course(cid, db_path=temp_db)
    assert ok is True

    deleted = fetch_one("SELECT * FROM courses WHERE id = ?", (cid,), db_path=temp_db)
    assert deleted is None


def test_admin_metrics_calculation(temp_db):
    """Verifies that platform overview metrics compute real non-trivial numbers."""
    metrics = get_admin_metrics(db_path=temp_db)
    assert metrics["total_students"] >= 1
    assert metrics["total_courses"] >= 20
    assert metrics["total_enrollments"] >= 1
    assert metrics["avg_rating"] >= 1.0
