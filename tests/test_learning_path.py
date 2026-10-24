"""
Unit tests for Personalized Learning Path generation:
- Prerequisite-aware topological ordering
- Timeline and schedule estimation
"""

import tempfile
import os
import pytest
from database.seed_data import seed_database
from modules.authentication import register_user
from modules.student_profile import update_student_profile
from modules.learning_path import build_learning_path


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_prerequisite_ordering_in_learning_path(temp_db):
    """
    Verifies that for Data Engineer role, foundational SQL/Python
    appear before Advanced Spark and ETL Pipelines.
    """
    _, _, uid = register_user("Path Student", "path@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    update_student_profile(
        user_id=uid,
        target_role="Data Engineer",
        preferred_difficulty="All",
        weekly_study_hours=10,
        selected_skills=[],
        selected_interests=["Data Engineering"],
        db_path=temp_db
    )

    path = build_learning_path(uid, db_path=temp_db)
    steps = path["steps"]
    assert len(steps) > 0

    step_codes = [s["course_code"] for s in steps]

    # Verify prerequisite order:
    # SQL101 must appear before SQL201 and DE101
    if "SQL101" in step_codes and "SQL201" in step_codes:
        assert step_codes.index("SQL101") < step_codes.index("SQL201")

    # PY101 must appear before ETL201
    if "PY101" in step_codes and "ETL201" in step_codes:
        assert step_codes.index("PY101") < step_codes.index("ETL201")

    # ETL201 must appear before SPARK301
    if "ETL201" in step_codes and "SPARK301" in step_codes:
        assert step_codes.index("ETL201") < step_codes.index("SPARK301")


def test_timeline_calculation(temp_db):
    """Verifies that estimated weeks = total hours / weekly hours."""
    _, _, uid = register_user("Timeline Student", "time@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    update_student_profile(
        user_id=uid,
        target_role="Data Analyst",
        preferred_difficulty="Beginner",
        weekly_study_hours=10,
        selected_skills=[],
        selected_interests=["Data Analysis"],
        db_path=temp_db
    )

    path = build_learning_path(uid, db_path=temp_db)
    assert path["total_hours"] > 0
    assert path["weekly_hours"] == 10
    expected_weeks = round(path["total_hours"] / 10.0, 1)
    assert path["estimated_weeks"] == expected_weeks
