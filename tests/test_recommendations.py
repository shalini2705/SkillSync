"""
Unit tests for the personalized recommendation engine:
- TF-IDF and Cosine similarity ranking
- Exclusion of completed courses
- Profile differentiation (different students receive different recommendations)
- Feedback loop influence
"""

import tempfile
import os
import pytest
from database.seed_data import seed_database
from modules.authentication import register_user
from modules.student_profile import update_student_profile
from modules.recommendation_engine import get_recommendations
from modules.enrollment import enroll_course, update_enrollment_status
from modules.feedback import submit_rating


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_recommendation_ranking_and_structure(temp_db):
    """Verifies that recommendations return ranked list with explainability."""
    # Register test student
    _, _, uid = register_user("Data Student", "datastudent@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    update_student_profile(
        user_id=uid,
        target_role="Data Analyst",
        preferred_difficulty="Beginner",
        weekly_study_hours=10,
        selected_skills=["Excel"],
        selected_interests=["Data Analysis"],
        db_path=temp_db
    )

    recs, diag = get_recommendations(uid, top_n=5, db_path=temp_db)
    assert len(recs) > 0
    assert diag["status"] == "success"

    # Verify fields in each recommendation
    for r in recs:
        assert "course_code" in r
        assert "title" in r
        assert "relevance_score" in r
        assert 0.0 <= r["relevance_score"] <= 100.0
        assert "explanation" in r
        assert len(r["explanation"]) > 0

    # Verify descending sort order by relevance score
    scores = [r["relevance_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)


def test_exclusion_of_completed_courses(temp_db):
    """Verifies that courses marked as Completed are strictly excluded from new recommendations."""
    _, _, uid = register_user("Exclusion Student", "excl@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    update_student_profile(
        user_id=uid,
        target_role="Data Analyst",
        preferred_difficulty="All",
        weekly_study_hours=10,
        selected_skills=["Excel"],
        selected_interests=["Data Analysis"],
        db_path=temp_db
    )

    # Get initial recommendations
    initial_recs, _ = get_recommendations(uid, top_n=5, db_path=temp_db)
    top_course = initial_recs[0]
    top_cid = top_course["id"]

    # Enroll in top course and mark as completed
    enroll_course(uid, top_cid, db_path=temp_db)
    update_enrollment_status(uid, top_cid, "Completed", db_path=temp_db)

    # Re-run recommendations
    updated_recs, _ = get_recommendations(uid, top_n=5, db_path=temp_db)
    updated_cids = {r["id"] for r in updated_recs}

    # The completed course must NOT appear in updated recommendations
    assert top_cid not in updated_cids, f"Completed course {top_course['course_code']} should have been excluded."


def test_different_profiles_receive_different_recommendations(temp_db):
    """
    Verifies that a student targeting 'Data Analyst' and a student targeting 'Web Developer'
    receive distinct, role-aligned recommendations.
    """
    # Student 1: Data Analyst
    _, _, uid1 = register_user("Data Aspirant", "analyst@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    update_student_profile(
        user_id=uid1,
        target_role="Data Analyst",
        preferred_difficulty="Beginner",
        weekly_study_hours=10,
        selected_skills=["Excel"],
        selected_interests=["Data Analysis"],
        db_path=temp_db
    )

    # Student 2: Web Developer
    _, _, uid2 = register_user("Web Aspirant", "webdev@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    update_student_profile(
        user_id=uid2,
        target_role="Web Developer",
        preferred_difficulty="Beginner",
        weekly_study_hours=10,
        selected_skills=["HTML"],
        selected_interests=["Web Development"],
        db_path=temp_db
    )

    recs_data, _ = get_recommendations(uid1, top_n=3, db_path=temp_db)
    recs_web, _ = get_recommendations(uid2, top_n=3, db_path=temp_db)

    data_codes = [r["course_code"] for r in recs_data]
    web_codes = [r["course_code"] for r in recs_web]

    # Data Analyst should see SQL/Python/Excel/BI, Web Dev should see HTML/CSS/JS/React
    assert data_codes != web_codes, "Different career goals must produce different top recommendations."
    assert any(c in ["SQL101", "PY101", "EXCEL101", "STAT101"] for c in data_codes)
    assert any(c in ["WEB101", "JS101", "REACT201"] for c in web_codes)
