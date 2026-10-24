"""
Validation utilities for inputs across registration, login, course management, and feedback.
"""

import re
from typing import Tuple, List


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_registration(name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
    """Validates student/user registration form fields."""
    if not name or len(name.strip()) < 2:
        return False, "Full name must be at least 2 characters long."

    if not email or not EMAIL_REGEX.match(email.strip()):
        return False, "Please enter a valid email address (e.g., student@example.com)."

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if password != confirm_password:
        return False, "Passwords do not match."

    return True, ""


def validate_course_data(
    course_code: str,
    title: str,
    description: str,
    category: str,
    difficulty: str,
    duration: int,
    skills: List[str]
) -> Tuple[bool, str]:
    """Validates course creation and update inputs."""
    if not course_code or len(course_code.strip()) < 2 or len(course_code.strip()) > 15:
        return False, "Course code must be between 2 and 15 characters (e.g., CS101)."

    if not title or len(title.strip()) < 3:
        return False, "Course title must be at least 3 characters long."

    if not description or len(description.strip()) < 10:
        return False, "Description must be at least 10 characters long to guide students."

    if not category or len(category.strip()) < 2:
        return False, "Please select or provide a valid category."

    if difficulty not in ["Beginner", "Intermediate", "Advanced"]:
        return False, "Difficulty must be one of: Beginner, Intermediate, Advanced."

    try:
        dur = int(duration)
        if dur <= 0 or dur > 500:
            return False, "Estimated duration must be between 1 and 500 hours."
    except (ValueError, TypeError):
        return False, "Duration must be a valid positive whole number."

    if not skills:
        return False, "Select at least one skill that this course teaches."

    return True, ""


def validate_rating_input(rating: int, review: str = "") -> Tuple[bool, str]:
    """Validates course feedback and star ratings."""
    try:
        r = int(rating)
        if r < 1 or r > 5:
            return False, "Rating must be an integer between 1 and 5 stars."
    except (ValueError, TypeError):
        return False, "Rating must be a numerical score from 1 to 5."

    if review and len(review.strip()) > 1000:
        return False, "Review text cannot exceed 1000 characters."

    return True, ""
