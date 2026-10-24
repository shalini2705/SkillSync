"""
Administrator Dashboard and Course Management module.
Provides:
- Key platform metrics (students, courses, enrollments, completions, average ratings)
- Plotly interactive charts (enrollments, ratings, category breakdown, role-skill coverage)
- Full Course CRUD (Create, Read, Update, Delete) with validation and transaction support
- Role-Skill requirement management
- Enforces strict role-based access control (admin only)
"""

from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database.db import fetch_all, fetch_one, execute_query, execute_insert, get_db_cursor
from utils.validators import validate_course_data
from modules.course_catalog import get_all_categories, get_courses
from modules.student_profile import get_all_skills, get_all_career_roles


def get_admin_metrics(db_path: str = None) -> Dict:
    """Calculates platform-wide counts and statistics."""
    total_students = fetch_one("SELECT COUNT(*) as cnt FROM users WHERE role = 'student'", db_path=db_path)["cnt"]
    total_courses = fetch_one("SELECT COUNT(*) as cnt FROM courses", db_path=db_path)["cnt"]
    total_enrollments = fetch_one("SELECT COUNT(*) as cnt FROM enrollments", db_path=db_path)["cnt"]
    total_completions = fetch_one("SELECT COUNT(*) as cnt FROM enrollments WHERE status = 'Completed'", db_path=db_path)["cnt"]
    avg_rating_row = fetch_one("SELECT AVG(rating) as avg_r FROM ratings", db_path=db_path)
    avg_rating = round(avg_rating_row["avg_r"], 2) if avg_rating_row["avg_r"] else 0.0

    return {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_enrollments": total_enrollments,
        "total_completions": total_completions,
        "avg_rating": avg_rating
    }


def add_course(
    course_code: str,
    title: str,
    description: str,
    category: str,
    difficulty: str,
    duration: int,
    skills: List[str],
    target_roles: List[str],
    prereq_codes: List[str] = None,
    db_path: str = None
) -> tuple[bool, str]:
    """Inserts a new course with skill and target role mappings in a single transaction."""
    is_valid, err = validate_course_data(course_code, title, description, category, difficulty, duration, skills)
    if not is_valid:
        return False, err

    clean_code = course_code.strip().upper()

    # Check for duplicate course code
    existing = fetch_one("SELECT id FROM courses WHERE course_code = ?", (clean_code,), db_path=db_path)
    if existing:
        return False, f"Course code '{clean_code}' already exists. Use a unique code."

    try:
        with get_db_cursor(db_path, commit=True) as cursor:
            # 1. Insert course
            cursor.execute(
                """
                INSERT INTO courses (course_code, title, description, category, difficulty_level, estimated_duration_hours)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (clean_code, title.strip(), description.strip(), category.strip(), difficulty, duration)
            )
            course_id = cursor.lastrowid

            # 2. Insert Skills
            for s_name in skills:
                cursor.execute("SELECT id FROM skills WHERE name = ?", (s_name,))
                s_row = cursor.fetchone()
                if s_row:
                    cursor.execute("INSERT OR IGNORE INTO course_skills (course_id, skill_id) VALUES (?, ?)", (course_id, s_row["id"]))

            # 3. Insert Target Roles
            for r_name in target_roles:
                cursor.execute("SELECT id FROM career_roles WHERE name = ?", (r_name,))
                r_row = cursor.fetchone()
                if r_row:
                    cursor.execute("INSERT OR IGNORE INTO course_target_roles (course_id, role_id) VALUES (?, ?)", (course_id, r_row["id"]))

            # 4. Insert Prerequisites
            if prereq_codes:
                for p_code in prereq_codes:
                    cursor.execute("SELECT id FROM courses WHERE course_code = ?", (p_code.strip().upper(),))
                    p_row = cursor.fetchone()
                    if p_row:
                        cursor.execute(
                            "INSERT OR IGNORE INTO course_prerequisites (course_id, prerequisite_course_id, note) VALUES (?, ?, ?)",
                            (course_id, p_row["id"], f"Prerequisite: {p_code}")
                        )

        return True, f"Course [{clean_code}] successfully added to catalog!"
    except Exception as e:
        return False, f"Failed to add course: {str(e)}"


def update_course(
    course_id: int,
    title: str,
    description: str,
    category: str,
    difficulty: str,
    duration: int,
    skills: List[str],
    target_roles: List[str],
    db_path: str = None
) -> tuple[bool, str]:
    """Updates an existing course record and its mappings."""
    try:
        with get_db_cursor(db_path, commit=True) as cursor:
            cursor.execute(
                """
                UPDATE courses
                SET title = ?, description = ?, category = ?, difficulty_level = ?, estimated_duration_hours = ?
                WHERE id = ?
                """,
                (title.strip(), description.strip(), category.strip(), difficulty, duration, course_id)
            )

            # Update skills
            cursor.execute("DELETE FROM course_skills WHERE course_id = ?", (course_id,))
            for s_name in skills:
                cursor.execute("SELECT id FROM skills WHERE name = ?", (s_name,))
                s_row = cursor.fetchone()
                if s_row:
                    cursor.execute("INSERT OR IGNORE INTO course_skills (course_id, skill_id) VALUES (?, ?)", (course_id, s_row["id"]))

            # Update target roles
            cursor.execute("DELETE FROM course_target_roles WHERE course_id = ?", (course_id,))
            for r_name in target_roles:
                cursor.execute("SELECT id FROM career_roles WHERE name = ?", (r_name,))
                r_row = cursor.fetchone()
                if r_row:
                    cursor.execute("INSERT OR IGNORE INTO course_target_roles (course_id, role_id) VALUES (?, ?)", (course_id, r_row["id"]))

        return True, "Course updated successfully!"
    except Exception as e:
        return False, f"Failed to update course: {str(e)}"


def delete_course(course_id: int, db_path: str = None) -> tuple[bool, str]:
    """Deletes a course and cascades related mappings."""
    try:
        execute_query("DELETE FROM courses WHERE id = ?", (course_id,), db_path=db_path)
        return True, "Course deleted successfully from the catalog."
    except Exception as e:
        return False, f"Failed to delete course: {str(e)}"


def render_admin_dashboard():
    """Renders the comprehensive Administrator Portal."""
    st.markdown("## 🛡️ Administrator Analytics & Course Management")
    st.caption("Monitor learner engagement, manage course offerings, and analyze skill coverage across career pathways.")

    tab_overview, tab_catalog_mgmt, tab_roles = st.tabs([
        "📈 Analytics & Insights",
        "⚙️ Course Catalog Management",
        "🎯 Career Roles & Skill Mapping"
    ])

    with tab_overview:
        metrics = get_admin_metrics()

        # Top 5 Metric Cards
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Students</div>
                    <div class="metric-value">{metrics['total_students']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f"""
                <div class="metric-card" style="border-left-color:#3B82F6;">
                    <div class="metric-title">Courses</div>
                    <div class="metric-value">{metrics['total_courses']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f"""
                <div class="metric-card" style="border-left-color:#10B981;">
                    <div class="metric-title">Enrollments</div>
                    <div class="metric-value">{metrics['total_enrollments']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m4:
            st.markdown(
                f"""
                <div class="metric-card" style="border-left-color:#8B5CF6;">
                    <div class="metric-title">Completions</div>
                    <div class="metric-value">{metrics['total_completions']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m5:
            st.markdown(
                f"""
                <div class="metric-card" style="border-left-color:#F59E0B;">
                    <div class="metric-title">Avg Rating</div>
                    <div class="metric-value">★ {metrics['avg_rating']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br/>", unsafe_allow_html=True)

        # Plotly Visualizations Row 1
        all_courses = get_courses(sort_by="Most Enrolled")
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown("##### 👥 Most Enrolled Courses")
            top_enrolled = sorted(all_courses, key=lambda x: x["enrollment_count"], reverse=True)[:6]
            if top_enrolled and any(c["enrollment_count"] > 0 for c in top_enrolled):
                df_enr = [
                    {"Course": f"[{c['course_code']}] {c['title'][:25]}...", "Enrollments": c["enrollment_count"]}
                    for c in top_enrolled
                ]
                fig_enr = px.bar(
                    df_enr,
                    x="Enrollments",
                    y="Course",
                    orientation="h",
                    color="Enrollments",
                    color_continuous_scale="Blues"
                )
                fig_enr.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(l=10, r=10, t=20, b=20))
                st.plotly_chart(fig_enr, use_container_width=True)
            else:
                st.info("No enrollment activity recorded yet.")

        with col_c2:
            st.markdown("##### ⭐ Top Rated Courses")
            rated_courses = [c for c in all_courses if c["avg_rating"] > 0]
            rated_courses.sort(key=lambda x: x["avg_rating"], reverse=True)
            top_rated = rated_courses[:6]
            if top_rated:
                df_rate = [
                    {"Course": f"[{c['course_code']}] {c['title'][:25]}...", "Rating": c["avg_rating"]}
                    for c in top_rated
                ]
                fig_rate = px.bar(
                    df_rate,
                    x="Rating",
                    y="Course",
                    orientation="h",
                    color="Rating",
                    color_continuous_scale="Viridis",
                    range_x=[0, 5]
                )
                fig_rate.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(l=10, r=10, t=20, b=20))
                st.plotly_chart(fig_rate, use_container_width=True)
            else:
                st.info("No course ratings recorded yet.")

        # Row 2: Category Breakdown and Skill Coverage by Role
        col_c3, col_c4 = st.columns(2)

        with col_c3:
            st.markdown("##### 📂 Course Catalog by Category")
            cat_counts = {}
            for c in all_courses:
                cat_counts[c["category"]] = cat_counts.get(c["category"], 0) + 1
            if cat_counts:
                fig_cat = px.pie(
                    values=list(cat_counts.values()),
                    names=list(cat_counts.keys()),
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_cat.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=20))
                st.plotly_chart(fig_cat, use_container_width=True)

        with col_c4:
            st.markdown("##### 🎯 Role Catalog Skill-Coverage")
            # Calculate how many of each role's required skills have at least 1 course teaching it
            roles = get_all_career_roles()
            role_cov_data = []
            for r in roles:
                role_skills = fetch_all(
                    "SELECT s.name FROM role_skills rs JOIN skills s ON rs.skill_id = s.id WHERE rs.role_id = ? AND rs.importance = 'Required'",
                    (r["id"],)
                )
                req_names = [s["name"].lower() for s in role_skills]
                taught_skills = set()
                for c in all_courses:
                    for s in c.get("skills", []):
                        taught_skills.add(s.lower())

                covered = sum(1 for s in req_names if s in taught_skills)
                pct = round((covered / len(req_names) * 100), 1) if req_names else 100.0
                role_cov_data.append({"Role": r["name"], "Catalog Coverage (%)": pct})

            if role_cov_data:
                fig_role_cov = px.bar(
                    role_cov_data,
                    x="Role",
                    y="Catalog Coverage (%)",
                    color="Catalog Coverage (%)",
                    color_continuous_scale="Teal",
                    range_y=[0, 100]
                )
                fig_role_cov.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=20))
                st.plotly_chart(fig_role_cov, use_container_width=True)

    with tab_catalog_mgmt:
        sub_view, sub_add, sub_edit = st.tabs(["📋 View & Delete Courses", "➕ Add New Course", "✏️ Edit Course"])

        with sub_view:
            st.markdown("##### Existing Course Catalog")
            catalog = get_courses(sort_by="Default")
            for c in catalog:
                cid = c["id"]
                with st.expander(f"[{c['course_code']}] {c['title']} ({c['difficulty_level']} | {c['category']})"):
                    st.write(f"**Description:** {c['description']}")
                    st.write(f"**Duration:** {c['estimated_duration_hours']} hours | **Enrollments:** {c['enrollment_count']} | **Rating:** {c['avg_rating']}/5")
                    st.write(f"**Skills:** {', '.join(c['skills'])}")
                    st.write(f"**Target Roles:** {', '.join(c['target_roles'])}")
                    if st.button(f"🗑️ Delete Course [{c['course_code']}]", key=f"del_{cid}", type="secondary"):
                        del_ok, del_msg = delete_course(cid)
                        if del_ok:
                            st.success(del_msg)
                            st.rerun()
                        else:
                            st.error(del_msg)

        with sub_add:
            st.markdown("##### Add New Course to Repository")
            all_skills = get_all_skills()
            all_roles = [r["name"] for r in get_all_career_roles()]
            all_course_codes = [c["course_code"] for c in get_courses()]

            with st.form("add_course_form"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    new_code = st.text_input("Course Code *", placeholder="e.g. CLOUD101")
                    new_title = st.text_input("Course Title *", placeholder="e.g. AWS Cloud Architecture")
                    new_cat = st.text_input("Category *", placeholder="e.g. Cloud Computing")
                    new_diff = st.selectbox("Difficulty *", ["Beginner", "Intermediate", "Advanced"])
                    new_dur = st.number_input("Estimated Duration (hours) *", min_value=1, max_value=300, value=20)

                with col_a2:
                    new_skills = st.multiselect("Skills Taught *", options=all_skills)
                    new_roles_sel = st.multiselect("Target Career Roles", options=all_roles)
                    new_prereqs = st.multiselect("Prerequisite Courses", options=all_course_codes)
                    new_desc = st.text_area("Detailed Description *", placeholder="Comprehensive syllabus and learning outcomes...")

                submit_add = st.form_submit_button("Save and Publish Course", type="primary", use_container_width=True)

                if submit_add:
                    ok, msg = add_course(
                        course_code=new_code,
                        title=new_title,
                        description=new_desc,
                        category=new_cat,
                        difficulty=new_diff,
                        duration=new_dur,
                        skills=new_skills,
                        target_roles=new_roles_sel,
                        prereq_codes=new_prereqs
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with sub_edit:
            st.markdown("##### Edit Existing Course Metadata")
            courses_list = get_courses()
            course_options = {f"[{c['course_code']}] {c['title']}": c for c in courses_list}
            selected_label = st.selectbox("Select Course to Edit", options=list(course_options.keys()))

            if selected_label:
                selected_course = course_options[selected_label]
                all_skills = get_all_skills()
                all_roles = [r["name"] for r in get_all_career_roles()]

                with st.form("edit_course_form"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        edit_title = st.text_input("Title", value=selected_course["title"])
                        edit_cat = st.text_input("Category", value=selected_course["category"])
                        diff_opts = ["Beginner", "Intermediate", "Advanced"]
                        diff_idx = diff_opts.index(selected_course["difficulty_level"]) if selected_course["difficulty_level"] in diff_opts else 0
                        edit_diff = st.selectbox("Difficulty", diff_opts, index=diff_idx)
                        edit_dur = st.number_input("Duration (hours)", min_value=1, max_value=300, value=int(selected_course["estimated_duration_hours"]))

                    with col_e2:
                        edit_skills = st.multiselect("Skills Taught", options=all_skills, default=[s for s in selected_course["skills"] if s in all_skills])
                        edit_roles = st.multiselect("Target Roles", options=all_roles, default=[r for r in selected_course["target_roles"] if r in all_roles])
                        edit_desc = st.text_area("Description", value=selected_course["description"])

                    submit_edit = st.form_submit_button("Update Course", type="primary", use_container_width=True)

                    if submit_edit:
                        ok, msg = update_course(
                            course_id=selected_course["id"],
                            title=edit_title,
                            description=edit_desc,
                            category=edit_cat,
                            difficulty=edit_diff,
                            duration=edit_dur,
                            skills=edit_skills,
                            target_roles=edit_roles
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    with tab_roles:
        st.markdown("##### Career Roles & Skill Requirements Matrix")
        st.caption("Define the core mandatory skills and recommended electives for each industry career role.")

        all_roles_data = get_all_career_roles()
        for role in all_roles_data:
            role_skills = fetch_all(
                """
                SELECT s.name, rs.importance
                FROM role_skills rs
                JOIN skills s ON rs.skill_id = s.id
                WHERE rs.role_id = ?
                ORDER BY rs.importance DESC, s.name ASC
                """,
                (role["id"],)
            )
            reqs = [s["name"] for s in role_skills if s["importance"] == "Required"]
            recs = [s["name"] for s in role_skills if s["importance"] == "Recommended"]

            with st.expander(f"🎯 {role['name']}"):
                st.write(f"*{role['description']}*")
                st.markdown(f"**Required Core Skills ({len(reqs)}):** {', '.join(reqs) if reqs else 'None specified'}")
                st.markdown(f"**Recommended Skills ({len(recs)}):** {', '.join(recs) if recs else 'None specified'}")
