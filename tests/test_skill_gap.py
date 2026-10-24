"""
Unit tests for Skill-Gap Analysis:
- Skills possessed vs missing
- Mathematical coverage percentage
- Course mapping for missing skills
"""

import tempfile
import os
import pytest
from database.seed_data import seed_database
from modules.authentication import register_user
from modules.student_profile import update_student_profile
from modules.skill_gap_analysis import calculate_skill_gap


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_skill_gap_calculation(temp_db):
    """Verifies skill gap logic when student possesses partial skills for Data Analyst."""
    _, _, uid = register_user("Gap Student", "gap@test.com", "Pass123!", "Pass123!", db_path=temp_db)

    # Data Analyst role requires: SQL, Excel, Python, Statistics, Data Visualization, Pandas (6 core skills)
    # Give the student 2 of these skills: Python and Excel
    update_student_profile(
        user_id=uid,
        target_role="Data Analyst",
        preferred_difficulty="Beginner",
        weekly_study_hours=10,
        selected_skills=["Python", "Excel"],
        selected_interests=["Data Analysis"],
        db_path=temp_db
    )

    gap = calculate_skill_gap(uid, db_path=temp_db)

    assert gap["target_role"] == "Data Analyst"
    assert "Python" in gap["possessed_required"]
    assert "Excel" in gap["possessed_required"]
    assert "SQL" in gap["missing_required"]
    assert "Statistics" in gap["missing_required"]

    # 2 out of 6 required skills = 33.3%
    assert gap["total_required_count"] == 6
    assert len(gap["possessed_required"]) == 2
    assert gap["coverage_percentage"] == 33.3

    # Check course recommendation exists for missing skill "SQL"
    sql_courses = gap["missing_skill_courses"].get("SQL", [])
    assert len(sql_courses) > 0
    sql_course_codes = [c["course_code"] for c in sql_courses]
    assert "SQL101" in sql_course_codes
