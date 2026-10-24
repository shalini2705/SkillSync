"""
Course Enrollment module.
Handles enrolling in courses, status progression (Enrolled -> In Progress -> Completed),
and duplicate enrollment prevention.
"""

from typing import Tuple, List, Dict
import streamlit as st
from database.db import fetch_one, fetch_all, execute_insert, execute_query


def enroll_course(user_id: int, course_id: int, db_path: str = None) -> Tuple[bool, str]:
    """
    Enrolls a student into a course.
    Prevents duplicate active enrollments.
    """
    # Check if already enrolled
    existing = fetch_one(
        "SELECT id, status FROM enrollments WHERE user_id = ? AND course_id = ?",
        (user_id, course_id),
        db_path=db_path
    )
    if existing:
        if existing["status"] == "Completed":
            return False, "You have already completed this course previously."
        return False, f"You are already actively enrolled in this course (Status: {existing['status']})."

    try:
        execute_insert(
            "INSERT INTO enrollments (user_id, course_id, status) VALUES (?, ?, 'Enrolled')",
            (user_id, course_id),
            db_path=db_path
        )
        return True, "Successfully enrolled in the course!"
    except Exception as e:
        return False, f"Enrollment failed: {str(e)}"


def update_enrollment_status(
    user_id: int,
    course_id: int,
    new_status: str,
    db_path: str = None
) -> Tuple[bool, str]:
    """
    Updates the enrollment status of a student.
    When marked as 'Completed', sets completed_at timestamp.
    """
    if new_status not in ["Enrolled", "In Progress", "Completed"]:
        return False, "Invalid enrollment status."

    try:
        if new_status == "Completed":
            execute_query(
                "UPDATE enrollments SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?",
                (new_status, user_id, course_id),
                db_path=db_path
            )
        else:
            execute_query(
                "UPDATE enrollments SET status = ?, completed_at = NULL WHERE user_id = ? AND course_id = ?",
                (new_status, user_id, course_id),
                db_path=db_path
            )
        return True, f"Status updated to '{new_status}' successfully!"
    except Exception as e:
        return False, f"Status update failed: {str(e)}"


def get_student_enrollments(user_id: int, db_path: str = None) -> List[Dict]:
    """Retrieves all course enrollments for a student with ratings if completed."""
    rows = fetch_all(
        """
        SELECT 
            e.id as enrollment_id,
            e.course_id,
            c.course_code,
            c.title,
            c.category,
            c.difficulty_level,
            c.estimated_duration_hours,
            e.status,
            e.enrolled_at,
            e.completed_at,
            r.rating,
            r.review,
            r.created_at as rated_at
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN ratings r ON (e.course_id = r.course_id AND e.user_id = r.user_id)
        WHERE e.user_id = ?
        ORDER BY 
            CASE e.status
                WHEN 'In Progress' THEN 1
                WHEN 'Enrolled' THEN 2
                WHEN 'Completed' THEN 3
            END,
            e.enrolled_at DESC
        """,
        (user_id,),
        db_path=db_path
    )
    return rows
