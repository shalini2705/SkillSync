"""
Feedback and Course Rating module.
Enforces rules:
- Students can only submit feedback for courses marked as 'Completed'.
- Rating score must be between 1 and 5.
- Submissions dynamically update the course feedback loop.
"""

from typing import Tuple, List, Dict
import streamlit as st

from database.db import fetch_one, execute_query
from modules.enrollment import get_student_enrollments, update_enrollment_status
from utils.validators import validate_rating_input
from utils.helpers import get_difficulty_badge, render_stars


def submit_rating(
    user_id: int,
    course_id: int,
    rating: int,
    review: str = "",
    db_path: str = None
) -> Tuple[bool, str]:
    """
    Submits or updates a star rating and review.
    Enforces check: student MUST have completed the course first.
    """
    # 1. Check completion requirement
    enrollment = fetch_one(
        "SELECT id, status FROM enrollments WHERE user_id = ? AND course_id = ?",
        (user_id, course_id),
        db_path=db_path
    )
    if not enrollment:
        return False, "You must be enrolled in this course before you can submit a rating."

    if enrollment["status"] != "Completed":
        return False, "You can only rate and review courses you have marked as 'Completed'."

    # 2. Validate input
    is_valid, err_msg = validate_rating_input(rating, review)
    if not is_valid:
        return False, err_msg

    try:
        execute_query(
            """
            INSERT INTO ratings (user_id, course_id, rating, review, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, course_id) DO UPDATE SET
                rating = excluded.rating,
                review = excluded.review,
                created_at = CURRENT_TIMESTAMP
            """,
            (user_id, course_id, rating, review.strip()),
            db_path=db_path
        )
        return True, "Thank you! Your feedback has been recorded and will refine future recommendations."
    except Exception as e:
        return False, f"Failed to submit feedback: {str(e)}"


def render_my_enrollments_page(user_id: int):
    """Renders the student's enrollments, status controls, and rating submission cards."""
    st.markdown("## 🎓 My Enrolled Courses & Learning Progress")
    st.caption("Track your current learning progress, update milestone completion, and share feedback.")

    enrollments = get_student_enrollments(user_id)

    if not enrollments:
        st.info("You haven't enrolled in any courses yet. Browse the Course Catalog or Recommended Courses to begin!")
        return

    # Tabs for Active vs Completed
    active_courses = [e for e in enrollments if e["status"] != "Completed"]
    completed_courses = [e for e in enrollments if e["status"] == "Completed"]

    tab_active, tab_completed = st.tabs([
        f"📖 In Progress & Enrolled ({len(active_courses)})",
        f"✅ Completed Courses ({len(completed_courses)})"
    ])

    with tab_active:
        if not active_courses:
            st.success("No active courses pending! Explore new recommendations or complete your journey.")
        else:
            for item in active_courses:
                cid = item["course_id"]
                diff_badge = get_difficulty_badge(item["difficulty_level"])
                status_color = "#2563EB" if item["status"] == "In Progress" else "#64748B"

                with st.container():
                    col_info, col_status = st.columns([3, 2])
                    with col_info:
                        st.markdown(
                            f"""
                            <h4 style="margin:0 0 0.25rem 0; color:#1E3A8A;">[{item['course_code']}] {item['title']}</h4>
                            <div style="font-size:0.85rem; color:#475569;">
                                {diff_badge} &nbsp;•&nbsp; 
                                <strong>Category:</strong> {item['category']} &nbsp;•&nbsp; 
                                <strong>Duration:</strong> {item['estimated_duration_hours']} hrs
                            </div>
                            <div style="margin-top:0.35rem;">
                                <span style="background-color:#EFF6FF; color:{status_color}; padding:0.2rem 0.6rem; border-radius:4px; font-weight:600; font-size:0.82rem; border:1px solid #BFDBFE;">
                                    Status: {item['status']}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col_status:
                        st.markdown("**Update Status:**")
                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            if item["status"] == "Enrolled":
                                if st.button("Start Learning", key=f"btn_start_{cid}", use_container_width=True):
                                    success, msg = update_enrollment_status(user_id, cid, "In Progress")
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                        with col_s2:
                            if st.button("Mark Completed", key=f"btn_comp_{cid}", type="primary", use_container_width=True):
                                success, msg = update_enrollment_status(user_id, cid, "Completed")
                                if success:
                                    st.success("Congratulations on completing this course! You can now rate it.")
                                    st.rerun()

                    st.markdown("<hr style='margin:0.75rem 0; border:0; border-top:1px solid #E2E8F0;'/>", unsafe_allow_html=True)

    with tab_completed:
        if not completed_courses:
            st.info("No courses marked as completed yet. Complete an enrolled course above to rate and review it.")
        else:
            for item in completed_courses:
                cid = item["course_id"]
                has_rated = item["rating"] is not None

                with st.container():
                    col_c_info, col_c_rate = st.columns([3, 2])
                    with col_c_info:
                        st.markdown(
                            f"""
                            <h4 style="margin:0 0 0.25rem 0; color:#15803D;">✅ [{item['course_code']}] {item['title']}</h4>
                            <div style="font-size:0.85rem; color:#475569;">
                                <strong>Category:</strong> {item['category']} &nbsp;•&nbsp; 
                                <strong>Completed On:</strong> {item['completed_at'] or 'Recently'}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if has_rated:
                            stars_txt = "★" * int(item["rating"]) + "☆" * (5 - int(item["rating"]))
                            st.markdown(
                                f"""
                                <div style="margin-top:0.4rem; background:#ECFDF5; border:1px solid #A7F3D0; padding:0.5rem 0.75rem; border-radius:6px;">
                                    <span style="color:#059669; font-weight:700;">Your Rating: {stars_txt} ({item['rating']}/5)</span><br/>
                                    <span style="color:#334155; font-size:0.85rem;"><em>"{item['review'] or 'No written comments.'}"</em></span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                    with col_c_rate:
                        expander_title = "✏️ Update Rating & Review" if has_rated else "⭐ Rate this Completed Course"
                        with st.expander(expander_title, expanded=not has_rated):
                            current_val = int(item["rating"]) if has_rated else 5
                            rating_val = st.slider(
                                "Rating Score (1-5 Stars)",
                                min_value=1,
                                max_value=5,
                                value=current_val,
                                key=f"star_slider_{cid}"
                            )
                            review_val = st.text_area(
                                "Written Feedback (Optional)",
                                value=item["review"] or "",
                                placeholder="How well did this course teach the skills? Was the pacing appropriate?",
                                key=f"rev_text_{cid}"
                            )
                            if st.button("Submit Feedback", key=f"sub_rev_{cid}", type="primary", use_container_width=True):
                                ok, msg = submit_rating(user_id, cid, rating_val, review_val)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                    st.markdown("<hr style='margin:0.75rem 0; border:0; border-top:1px solid #E2E8F0;'/>", unsafe_allow_html=True)
