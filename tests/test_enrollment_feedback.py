"""
Unit tests for course enrollment, completion status, and feedback/ratings validation.
"""

import tempfile
import os
import pytest
from database.seed_data import seed_database
from modules.authentication import register_user
from modules.enrollment import enroll_course, update_enrollment_status, get_student_enrollments
from modules.feedback import submit_rating
from database.db import fetch_one


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_enrollment_and_duplicate_prevention(temp_db):
    """Verifies that duplicate enrollments are rejected."""
    _, _, uid = register_user("Enr Student", "enr@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    course = fetch_one("SELECT id FROM courses LIMIT 1", db_path=temp_db)
    cid = course["id"]

    # First enrollment succeeds
    ok1, msg1 = enroll_course(uid, cid, db_path=temp_db)
    assert ok1 is True

    # Duplicate enrollment fails
    ok2, msg2 = enroll_course(uid, cid, db_path=temp_db)
    assert ok2 is False
    assert "already" in msg2.lower()


def test_rating_requires_completion(temp_db):
    """Ensures students cannot rate a course before completing it."""
    _, _, uid = register_user("Rating Student", "rating@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    course = fetch_one("SELECT id FROM courses LIMIT 1", db_path=temp_db)
    cid = course["id"]

    # Not enrolled yet -> Rating fails
    ok_not_enrolled, msg_not = submit_rating(uid, cid, 5, "Great!", db_path=temp_db)
    assert ok_not_enrolled is False

    # Enrolled but status is 'Enrolled' -> Rating fails
    enroll_course(uid, cid, db_path=temp_db)
    ok_inprog, msg_prog = submit_rating(uid, cid, 5, "Good!", db_path=temp_db)
    assert ok_inprog is False
    assert "marked as 'completed'" in msg_prog.lower()

    # Mark as Completed -> Rating succeeds
    update_enrollment_status(uid, cid, "Completed", db_path=temp_db)
    ok_comp, msg_comp = submit_rating(uid, cid, 5, "Mastered the concepts!", db_path=temp_db)
    assert ok_comp is True
    assert "recorded" in msg_comp.lower()


def test_rating_bounds_validation(temp_db):
    """Ensures rating value must be between 1 and 5."""
    _, _, uid = register_user("Bound Student", "bound@test.com", "Pass123!", "Pass123!", db_path=temp_db)
    course = fetch_one("SELECT id FROM courses LIMIT 1", db_path=temp_db)
    cid = course["id"]

    enroll_course(uid, cid, db_path=temp_db)
    update_enrollment_status(uid, cid, "Completed", db_path=temp_db)

    # Score of 0 -> should fail
    ok0, _ = submit_rating(uid, cid, 0, db_path=temp_db)
    assert ok0 is False

    # Score of 6 -> should fail
    ok6, _ = submit_rating(uid, cid, 6, db_path=temp_db)
    assert ok6 is False

    # Score of 4 -> valid
    ok4, _ = submit_rating(uid, cid, 4, db_path=temp_db)
    assert ok4 is True
