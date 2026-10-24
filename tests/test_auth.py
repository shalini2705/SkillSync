"""
Unit tests for user registration, duplicate email prevention,
password hashing, and authentication validation.
"""

import tempfile
import os
import pytest
from database.seed_data import seed_database
from modules.authentication import (
    register_user,
    authenticate_user,
    verify_password
)
from database.db import fetch_one


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_user_registration_success(temp_db):
    """Verifies that a new student can register with a hashed password."""
    email = "new.student@codegnan.com"
    success, msg, user_id = register_user(
        name="Aarav Gupta",
        email=email,
        password="ValidPassword123!",
        confirm_password="ValidPassword123!",
        role="student",
        db_path=temp_db
    )
    assert success is True
    assert user_id is not None

    # Check database record
    user = fetch_one("SELECT * FROM users WHERE id = ?", (user_id,), db_path=temp_db)
    assert user["email"] == email
    assert user["full_name"] == "Aarav Gupta"
    # Never stored plain-text password
    assert user["password_hash"] != "ValidPassword123!"
    assert verify_password("ValidPassword123!", user["password_hash"]) is True


def test_duplicate_email_rejection(temp_db):
    """Verifies that duplicate email registrations are strictly rejected."""
    email = "unique.student@codegnan.com"
    ok1, _, _ = register_user("First Student", email, "Password123!", "Password123!", "student", db_path=temp_db)
    assert ok1 is True

    # Attempt second registration with same email
    ok2, err2, uid2 = register_user("Second Student", email, "Password456!", "Password456!", "student", db_path=temp_db)
    assert ok2 is False
    assert uid2 is None
    assert "already exists" in err2.lower()


def test_login_validation(temp_db):
    """Tests correct authentication vs wrong password."""
    email = "login.test@codegnan.com"
    register_user("Login Tester", email, "CorrectPass123", "CorrectPass123", "student", db_path=temp_db)

    # Valid credentials
    ok, _, user_data = authenticate_user(email, "CorrectPass123", db_path=temp_db)
    assert ok is True
    assert user_data["email"] == email

    # Invalid password
    bad_ok, bad_msg, bad_data = authenticate_user(email, "WrongPassword", db_path=temp_db)
    assert bad_ok is False
    assert bad_data is None
    assert "Invalid email or password" in bad_msg


def test_admin_account_exists(temp_db):
    """Verifies default admin account is seeded and has 'admin' role."""
    admin = fetch_one("SELECT * FROM users WHERE role = 'admin'", db_path=temp_db)
    assert admin is not None
    assert admin["role"] == "admin"
