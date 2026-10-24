"""
Student profile management module.
Handles loading, viewing, and updating student skills, interests,
target career role, difficulty preferences, and study hours.
"""

from typing import Dict, List, Tuple
import streamlit as st
from database.db import fetch_all, fetch_one, get_db_cursor


def get_all_skills() -> List[str]:
    """Retrieves all skill names from the database."""
    rows = fetch_all("SELECT name FROM skills ORDER BY name ASC")
    return [r["name"] for r in rows]


def get_all_career_roles() -> List[Dict]:
    """Retrieves all career roles and their descriptions."""
    return fetch_all("SELECT id, name, description FROM career_roles ORDER BY name ASC")


def get_student_profile(user_id: int, db_path: str = None) -> Dict:
    """Fetches the complete profile information for a student."""
    # Basic profile
    profile = fetch_one(
        "SELECT target_role, preferred_difficulty, weekly_study_hours, updated_at FROM student_profiles WHERE user_id = ?",
        (user_id,),
        db_path=db_path
    )
    if not profile:
        profile = {
            "target_role": "Data Analyst",
            "preferred_difficulty": "All",
            "weekly_study_hours": 10,
            "updated_at": None
        }

    # Skills possessed
    skill_rows = fetch_all(
        """
        SELECT s.name 
        FROM skills s
        JOIN student_skills ss ON s.id = ss.skill_id
        WHERE ss.student_id = ?
        ORDER BY s.name ASC
        """,
        (user_id,),
        db_path=db_path
    )
    skills = [r["name"] for r in skill_rows]

    # Interests
    interest_rows = fetch_all(
        "SELECT interest FROM student_interests WHERE student_id = ? ORDER BY interest ASC",
        (user_id,),
        db_path=db_path
    )
    interests = [r["interest"] for r in interest_rows]

    # Completed courses
    completed_rows = fetch_all(
        """
        SELECT c.id, c.course_code, c.title, c.category, c.difficulty_level, e.completed_at, r.rating, r.review
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN ratings r ON (c.id = r.course_id AND r.user_id = e.user_id)
        WHERE e.user_id = ? AND e.status = 'Completed'
        ORDER BY e.completed_at DESC
        """,
        (user_id,),
        db_path=db_path
    )

    # Active / In-progress courses
    active_rows = fetch_all(
        """
        SELECT c.id, c.course_code, c.title, c.category, c.difficulty_level, e.status, e.enrolled_at
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        WHERE e.user_id = ? AND e.status != 'Completed'
        ORDER BY e.enrolled_at DESC
        """,
        (user_id,),
        db_path=db_path
    )

    return {
        "target_role": profile["target_role"],
        "preferred_difficulty": profile["preferred_difficulty"],
        "weekly_study_hours": profile["weekly_study_hours"],
        "updated_at": profile["updated_at"],
        "skills": skills,
        "interests": interests,
        "completed_courses": completed_rows,
        "active_courses": active_rows
    }


def update_student_profile(
    user_id: int,
    target_role: str,
    preferred_difficulty: str,
    weekly_study_hours: int,
    selected_skills: List[str],
    selected_interests: List[str],
    db_path: str = None
) -> Tuple[bool, str]:
    """Updates student profile preferences, skills, and interests transactionally."""
    try:
        with get_db_cursor(db_path, commit=True) as cursor:
            # 1. Update or Insert profile record
            cursor.execute(
                """
                INSERT INTO student_profiles (user_id, target_role, preferred_difficulty, weekly_study_hours, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    target_role = excluded.target_role,
                    preferred_difficulty = excluded.preferred_difficulty,
                    weekly_study_hours = excluded.weekly_study_hours,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, target_role, preferred_difficulty, weekly_study_hours)
            )

            # 2. Update student skills
            cursor.execute("DELETE FROM student_skills WHERE student_id = ?", (user_id,))
            for skill_name in selected_skills:
                cursor.execute("SELECT id FROM skills WHERE name = ?", (skill_name,))
                skill_row = cursor.fetchone()
                if skill_row:
                    cursor.execute(
                        "INSERT OR IGNORE INTO student_skills (student_id, skill_id) VALUES (?, ?)",
                        (user_id, skill_row["id"])
                    )

            # 3. Update student interests
            cursor.execute("DELETE FROM student_interests WHERE student_id = ?", (user_id,))
            for interest in selected_interests:
                if interest.strip():
                    cursor.execute(
                        "INSERT OR IGNORE INTO student_interests (student_id, interest) VALUES (?, ?)",
                        (user_id, interest.strip())
                    )

        return True, "Profile updated successfully! Recommendation engine has been updated."
    except Exception as e:
        return False, f"Failed to update profile: {str(e)}"


def render_student_profile(user_id: int):
    """Renders the Student Profile view and editor form."""
    st.markdown("## 👤 Student Profile & Learning Preferences")
    st.write("Customize your skill background, career aspirations, and learning pace to receive high-precision course recommendations.")

    profile = get_student_profile(user_id)
    all_skills = get_all_skills()
    roles = get_all_career_roles()
    role_names = [r["name"] for r in roles]

    common_interest_options = [
        "Data Analysis", "Machine Learning", "Deep Learning", "Web Development",
        "Backend Development", "Big Data", "Cloud Computing", "Databases", "DevOps",
        "API Design", "Data Visualization", "Automation"
    ]

    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            current_role_idx = role_names.index(profile["target_role"]) if profile["target_role"] in role_names else 0
            selected_role = st.selectbox(
                "🎯 Target Career Role",
                options=role_names,
                index=current_role_idx,
                help="Your target career will guide the skill-gap analysis and recommendation relevance ranking."
            )

            # Show role description
            selected_role_obj = next((r for r in roles if r["name"] == selected_role), None)
            if selected_role_obj and selected_role_obj.get("description"):
                st.caption(f"ℹ️ *{selected_role_obj['description']}*")

            weekly_hours = st.slider(
                "⏱️ Weekly Available Study Hours",
                min_value=2,
                max_value=40,
                value=int(profile["weekly_study_hours"] or 10),
                step=1,
                help="Used to calculate estimated schedule and completion timeline in your learning path."
            )

        with col2:
            diff_options = ["All", "Beginner", "Intermediate", "Advanced"]
            current_diff_idx = diff_options.index(profile["preferred_difficulty"]) if profile["preferred_difficulty"] in diff_options else 0
            selected_diff = st.selectbox(
                "📊 Preferred Course Difficulty",
                options=diff_options,
                index=current_diff_idx,
                help="Prioritize courses matching your preferred complexity level."
            )

            # Selected Interests
            selected_interests = st.multiselect(
                "💡 Areas of Interest / Topics",
                options=common_interest_options,
                default=[i for i in profile["interests"] if i in common_interest_options],
                help="Helps the TF-IDF engine surface matching elective topics."
            )

        st.markdown("---")
        st.markdown("#### 🛠️ Current Technical Skills")
        st.caption("Select skills you already possess or have acquired from prior education.")

        selected_skills = st.multiselect(
            "Select Your Current Skills",
            options=all_skills,
            default=[s for s in profile["skills"] if s in all_skills],
            placeholder="Choose skills (e.g. Python, SQL, Excel, HTML...)"
        )

        submit_btn = st.form_submit_button("💾 Save Profile Preferences", use_container_width=True)

        if submit_btn:
            success, msg = update_student_profile(
                user_id=user_id,
                target_role=selected_role,
                preferred_difficulty=selected_diff,
                weekly_study_hours=weekly_hours,
                selected_skills=selected_skills,
                selected_interests=selected_interests
            )
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    # Display Completed and In Progress summary cards
    st.markdown("---")
    col_comp, col_act = st.columns(2)

    with col_comp:
        st.markdown(f"#### ✅ Completed Courses ({len(profile['completed_courses'])})")
        if profile["completed_courses"]:
            for c in profile["completed_courses"]:
                st.markdown(
                    f"""
                    <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:0.75rem; margin-bottom:0.5rem;">
                        <strong>{c['course_code']} - {c['title']}</strong><br/>
                        <span style="font-size:0.85rem; color:#15803D;">Category: {c['category']} | Level: {c['difficulty_level']}</span><br/>
                        <span style="font-size:0.85rem; color:#047857;">Rating given: {'★'*int(c['rating']) if c['rating'] else 'Not rated'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No courses marked as completed yet. Complete enrolled courses to unlock ratings and refine recommendations.")

    with col_act:
        st.markdown(f"#### 📖 Currently Enrolled ({len(profile['active_courses'])})")
        if profile["active_courses"]:
            for c in profile["active_courses"]:
                st.markdown(
                    f"""
                    <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:0.75rem; margin-bottom:0.5rem;">
                        <strong>{c['course_code']} - {c['title']}</strong><br/>
                        <span style="font-size:0.85rem; color:#1D4ED8;">Status: {c['status']} | Level: {c['difficulty_level']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("You are not currently enrolled in any courses. Explore the Recommended Courses section to get started!")
