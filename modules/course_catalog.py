"""
Course Catalog module providing course retrieval, search, multi-faceted filtering,
sorting, and rendering course cards for both students and public visitors.
"""

from typing import List, Dict, Optional
import streamlit as st
from database.db import fetch_all, fetch_one
from utils.helpers import get_difficulty_badge, render_stars


def get_all_categories() -> List[str]:
    """Retrieves all distinct course categories present in the database."""
    rows = fetch_all("SELECT DISTINCT category FROM courses ORDER BY category ASC")
    return [r["category"] for r in rows]


def get_courses(
    search_query: str = "",
    category: str = "All",
    difficulty: str = "All",
    target_role: str = "All",
    sort_by: str = "Relevance",
    db_path: str = None
) -> List[Dict]:
    """
    Fetches courses with aggregated metadata (skills taught, prerequisites,
    target roles, average rating, and enrollment count) with filtering and sorting.
    """
    base_query = """
        SELECT 
            c.id,
            c.course_code,
            c.title,
            c.description,
            c.category,
            c.difficulty_level,
            c.estimated_duration_hours,
            COUNT(DISTINCT e.id) AS enrollment_count,
            AVG(r.rating) AS avg_rating,
            COUNT(DISTINCT r.id) AS rating_count
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN ratings r ON c.id = r.course_id
        LEFT JOIN course_target_roles ctr ON c.id = ctr.course_id
        LEFT JOIN career_roles cr ON ctr.role_id = cr.id
        WHERE 1=1
    """
    params = []

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        base_query += " AND (c.title LIKE ? OR c.description LIKE ? OR c.course_code LIKE ?)"
        params.extend([term, term, term])

    if category and category != "All":
        base_query += " AND c.category = ?"
        params.append(category)

    if difficulty and difficulty != "All":
        base_query += " AND c.difficulty_level = ?"
        params.append(difficulty)

    if target_role and target_role != "All":
        base_query += " AND cr.name = ?"
        params.append(target_role)

    base_query += " GROUP BY c.id"

    # Sorting options
    if sort_by == "Rating (High to Low)":
        base_query += " ORDER BY avg_rating DESC NULLS LAST, enrollment_count DESC"
    elif sort_by == "Most Enrolled":
        base_query += " ORDER BY enrollment_count DESC, c.title ASC"
    elif sort_by == "Duration (Short to Long)":
        base_query += " ORDER BY c.estimated_duration_hours ASC"
    elif sort_by == "Duration (Long to Short)":
        base_query += " ORDER BY c.estimated_duration_hours DESC"
    else:  # Title or Default
        base_query += " ORDER BY c.id ASC"

    courses = fetch_all(base_query, tuple(params), db_path=db_path)

    # Attach skills, target roles, and prerequisites to each course
    for course in courses:
        cid = course["id"]

        # Skills taught
        skills_rows = fetch_all(
            "SELECT s.name FROM skills s JOIN course_skills cs ON s.id = cs.skill_id WHERE cs.course_id = ?",
            (cid,),
            db_path=db_path
        )
        course["skills"] = [s["name"] for s in skills_rows]

        # Target roles
        roles_rows = fetch_all(
            "SELECT cr.name FROM career_roles cr JOIN course_target_roles ctr ON cr.id = ctr.role_id WHERE ctr.course_id = ?",
            (cid,),
            db_path=db_path
        )
        course["target_roles"] = [r["name"] for r in roles_rows]

        # Prerequisites
        prereq_rows = fetch_all(
            """
            SELECT cp.id as prereq_link_id, pc.id, pc.course_code, pc.title 
            FROM course_prerequisites cp
            JOIN courses pc ON cp.prerequisite_course_id = pc.id
            WHERE cp.course_id = ?
            """,
            (cid,),
            db_path=db_path
        )
        course["prerequisites"] = prereq_rows
        course["avg_rating"] = round(course["avg_rating"], 1) if course["avg_rating"] else 0.0

    return courses


def render_course_catalog(user_id: Optional[int] = None, on_enroll_callback = None):
    """Renders the interactive Course Catalog with search, filters, and enrollment actions."""
    st.markdown("## 📚 Course Catalog")
    st.caption("Explore our database-backed repository of sample courses across programming, data, and web development.")

    # Fetch filter options
    categories = ["All"] + get_all_categories()
    difficulties = ["All", "Beginner", "Intermediate", "Advanced"]
    from modules.student_profile import get_all_career_roles
    roles = ["All"] + [r["name"] for r in get_all_career_roles()]

    # Filter Bar
    with st.container():
        col_search, col_sort = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("🔍 Search courses by title, keywords, or code", placeholder="e.g. Python, SQL, React...")
        with col_sort:
            sort_by = st.selectbox(
                "↕️ Sort By",
                options=["Default", "Rating (High to Low)", "Most Enrolled", "Duration (Short to Long)", "Duration (Long to Short)"]
            )

        col_cat, col_diff, col_role = st.columns(3)
        with col_cat:
            selected_cat = st.selectbox("📂 Category", options=categories)
        with col_diff:
            selected_diff = st.selectbox("⚡ Difficulty", options=difficulties)
        with col_role:
            selected_role = st.selectbox("🎯 Target Career Role", options=roles)

    # Fetch courses based on active filters
    courses = get_courses(
        search_query=search_query,
        category=selected_cat,
        difficulty=selected_diff,
        target_role=selected_role,
        sort_by=sort_by
    )

    st.markdown(f"**Found {len(courses)} matching courses**")

    if not courses:
        st.warning("No courses match your filter criteria. Try clearing the search query or selecting 'All'.")
        return

    # Check user existing enrollments if logged in
    user_enrolled_cids = set()
    if user_id:
        enrolled_rows = fetch_all("SELECT course_id FROM enrollments WHERE user_id = ?", (user_id,))
        user_enrolled_cids = {r["course_id"] for r in enrolled_rows}

    # Grid / Card Display
    for course in courses:
        cid = course["id"]
        is_enrolled = cid in user_enrolled_cids

        with st.container():
            col_main, col_action = st.columns([4, 1])
            with col_main:
                diff_html = get_difficulty_badge(course["difficulty_level"])
                stars_html = render_stars(course["avg_rating"])

                st.markdown(
                    f"""
                    <div style="margin-top:0.5rem;">
                        <h4 style="margin:0 0 0.25rem 0; color:#1E3A8A;">
                            [{course['course_code']}] {course['title']}
                        </h4>
                        <div style="font-size:0.88rem; color:#475569; margin-bottom:0.5rem;">
                            {diff_html} &nbsp;•&nbsp; 
                            <strong>Category:</strong> {course['category']} &nbsp;•&nbsp; 
                            <strong>Duration:</strong> {course['estimated_duration_hours']} hrs &nbsp;•&nbsp; 
                            <span style="color:#D97706; font-weight:600;">{stars_html}</span> &nbsp;•&nbsp; 
                            <span>👥 {course['enrollment_count']} enrolled</span>
                        </div>
                        <p style="font-size:0.92rem; color:#334155; margin-bottom:0.5rem;">
                            {course['description']}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Skills badges
                skills_str = " ".join([f'<span class="skill-tag">🏷️ {s}</span>' for s in course["skills"]])
                st.markdown(f"<div style='margin-bottom:0.4rem;'>{skills_str}</div>", unsafe_allow_html=True)

                # Prerequisites info if any
                if course["prerequisites"]:
                    prereq_names = ", ".join([f"{p['course_code']}" for p in course["prerequisites"]])
                    st.caption(f"⚠️ *Prerequisites:* {prereq_names}")

            with col_action:
                st.write("")
                st.write("")
                if user_id:
                    if is_enrolled:
                        st.button("✓ Enrolled", key=f"cat_enrolled_{cid}", disabled=True, use_container_width=True)
                    else:
                        if st.button("➕ Enroll", key=f"cat_btn_{cid}", type="primary", use_container_width=True):
                            if on_enroll_callback:
                                on_enroll_callback(user_id, cid)
                else:
                    st.info("Log in to enroll")

            st.markdown("<hr style='margin: 0.8rem 0; border: 0; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)
