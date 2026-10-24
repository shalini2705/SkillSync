"""
Unit tests for database schema initialization and connection management.
"""

import tempfile
import os
import pytest
from database.db import get_connection, init_db, fetch_all, fetch_one
from database.seed_data import seed_database


@pytest.fixture
def temp_db():
    """Provides a fresh temporary SQLite database path for isolated testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_database_initialization_tables(temp_db):
    """Verifies that all required tables exist in the schema."""
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row["name"] for row in cursor.fetchall()}
    conn.close()

    expected_tables = {
        "users", "student_profiles", "skills", "career_roles", "role_skills",
        "student_skills", "student_interests", "courses", "course_skills",
        "course_prerequisites", "course_target_roles", "enrollments", "ratings"
    }
    for tbl in expected_tables:
        assert tbl in tables, f"Expected table '{tbl}' was not created."


def test_seed_courses_count(temp_db):
    """Verifies that at least 20 sample courses are seeded with required fields."""
    courses = fetch_all("SELECT * FROM courses", db_path=temp_db)
    assert len(courses) >= 20, f"Expected at least 20 courses, found {len(courses)}"

    for c in courses:
        assert c["course_code"] is not None
        assert c["title"] is not None
        assert c["category"] is not None
        assert c["difficulty_level"] in ["Beginner", "Intermediate", "Advanced"]
        assert c["estimated_duration_hours"] > 0
