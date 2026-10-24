"""
Skill-Gap Analysis module.
Evaluates student technical skills against role-specific requirements,
calculates coverage metrics, renders Plotly visual charts, and
identifies recommended courses to close targeted skill gaps.
"""

from typing import Dict, List, Tuple
import plotly.graph_objects as go
import streamlit as st

from database.db import fetch_all
from modules.student_profile import get_student_profile, get_all_career_roles


def calculate_skill_gap(user_id: int, target_role: str = None, db_path: str = None) -> Dict:
    """
    Computes skills possessed, missing skills, coverage percentage,
    and associated course mapping for closing the gaps.
    """
    profile = get_student_profile(user_id, db_path=db_path)
    role_to_check = target_role or profile.get("target_role", "Data Analyst")

    # Fetch required and recommended skills for this career role
    role_skills_rows = fetch_all(
        """
        SELECT s.name, rs.importance, cr.id as role_id, cr.description as role_desc
        FROM role_skills rs
        JOIN skills s ON rs.skill_id = s.id
        JOIN career_roles cr ON rs.role_id = cr.id
        WHERE cr.name = ?
        ORDER BY rs.importance DESC, s.name ASC
        """,
        (role_to_check,),
        db_path=db_path
    )

    student_skills = profile.get("skills", [])
    student_skills_lower = {s.lower() for s in student_skills}

    required_skills = []
    recommended_skills = []

    for r in role_skills_rows:
        s_name = r["name"]
        if r["importance"] == "Required":
            required_skills.append(s_name)
        else:
            recommended_skills.append(s_name)

    possessed_required = [s for s in required_skills if s.lower() in student_skills_lower]
    missing_required = [s for s in required_skills if s.lower() not in student_skills_lower]

    possessed_recommended = [s for s in recommended_skills if s.lower() in student_skills_lower]
    missing_recommended = [s for s in recommended_skills if s.lower() not in student_skills_lower]

    # Calculate coverage percentage
    # Coverage % = (possessed_required / total_required) * 100
    total_req = len(required_skills)
    coverage_pct = round((len(possessed_required) / total_req * 100), 1) if total_req > 0 else 100.0

    # Find courses that teach the missing skills
    missing_skill_courses = {}
    all_missing = missing_required + missing_recommended
    for missing_skill in all_missing:
        courses = fetch_all(
            """
            SELECT c.id, c.course_code, c.title, c.difficulty_level, c.estimated_duration_hours
            FROM courses c
            JOIN course_skills cs ON c.id = cs.course_id
            JOIN skills s ON cs.skill_id = s.id
            WHERE LOWER(s.name) = LOWER(?)
            ORDER BY c.difficulty_level ASC, c.estimated_duration_hours ASC
            """,
            (missing_skill,),
            db_path=db_path
        )
        missing_skill_courses[missing_skill] = courses

    return {
        "target_role": role_to_check,
        "total_required_count": total_req,
        "possessed_required": possessed_required,
        "missing_required": missing_required,
        "possessed_recommended": possessed_recommended,
        "missing_recommended": missing_recommended,
        "coverage_percentage": coverage_pct,
        "missing_skill_courses": missing_skill_courses,
        "all_student_skills": student_skills
    }


def render_skill_gap_page(user_id: int, on_enroll_callback = None):
    """Renders the comprehensive Skill-Gap Analysis dashboard with Plotly charts."""
    st.markdown("## 📊 Skill-Gap Analysis & Career Readiness")
    st.caption("Benchmark your current technical abilities against industry-standard requirements for your target career role.")

    profile = get_student_profile(user_id)
    roles = get_all_career_roles()
    role_names = [r["name"] for r in roles]

    # Role selector
    current_role = profile.get("target_role", "Data Analyst")
    current_idx = role_names.index(current_role) if current_role in role_names else 0

    col_role, col_info = st.columns([2, 3])
    with col_role:
        selected_role = st.selectbox(
            "Evaluate Against Role",
            options=role_names,
            index=current_idx
        )

    gap_data = calculate_skill_gap(user_id, target_role=selected_role)

    # Top summary metrics
    col_cov, col_pos, col_mis = st.columns(3)
    with col_cov:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Skill Coverage</div>
                <div class="metric-value" style="color: {'#16A34A' if gap_data['coverage_percentage'] >= 75 else '#2563EB' if gap_data['coverage_percentage'] >= 50 else '#DC2626'};">
                    {gap_data['coverage_percentage']}%
                </div>
                <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">
                    {len(gap_data['possessed_required'])} of {gap_data['total_required_count']} core skills met
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_pos:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #10B981;">
                <div class="metric-title">Acquired Core Skills</div>
                <div class="metric-value" style="color:#059669;">
                    {len(gap_data['possessed_required'])}
                </div>
                <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">
                    Verified in student profile
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_mis:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #EF4444;">
                <div class="metric-title">Missing Required Skills</div>
                <div class="metric-value" style="color:#DC2626;">
                    {len(gap_data['missing_required'])}
                </div>
                <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">
                    Courses available to bridge
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Visual Charts
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        # Gauge chart for coverage
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gap_data["coverage_percentage"],
            title={"text": f"<b>{selected_role} Readiness</b>", "font": {"size": 16, "color": "#1E3A8A"}},
            number={"suffix": "%", "font": {"size": 28, "color": "#0F172A"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
                "bar": {"color": "#2563EB"},
                "bgcolor": "#FFFFFF",
                "borderwidth": 1,
                "bordercolor": "#CBD5E1",
                "steps": [
                    {"range": [0, 40], "color": "#FEE2E2"},
                    {"range": [40, 70], "color": "#FEF3C7"},
                    {"range": [70, 100], "color": "#DCFCE7"}
                ],
                "threshold": {
                    "line": {"color": "#15803D", "width": 4},
                    "thickness": 0.75,
                    "value": 100
                }
            }
        ))
        fig_gauge.update_layout(
            height=260,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_chart2:
        # Bar breakdown of Required Skills
        all_req_skills = gap_data["possessed_required"] + gap_data["missing_required"]
        status_labels = ["Possessed" if s in gap_data["possessed_required"] else "Missing" for s in all_req_skills]
        colors = ["#10B981" if s in gap_data["possessed_required"] else "#EF4444" for s in all_req_skills]

        fig_bar = go.Figure(data=[
            go.Bar(
                x=all_req_skills,
                y=[1] * len(all_req_skills),
                marker_color=colors,
                text=status_labels,
                textposition="auto"
            )
        ])
        fig_bar.update_layout(
            title={"text": "<b>Required Skills Status</b>", "font": {"size": 16, "color": "#1E3A8A"}},
            yaxis=dict(visible=False),
            xaxis=dict(tickangle=-30),
            height=260,
            margin=dict(l=20, r=20, t=40, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Explanation formula note
    st.markdown(
        """
        <div class="alert-box alert-info" style="font-size:0.88rem;">
            📐 <strong>How Coverage is Calculated:</strong> 
            <code>Skill Coverage % = (Number of Possessed Required Skills / Total Required Skills for Role) × 100</code>.<br/>
            Recommended skills provide additional competitiveness but are tracked separately from baseline mandatory skills.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Skills Lists
    col_pos_list, col_mis_list = st.columns(2)

    with col_pos_list:
        st.markdown("### ✅ Skills You Already Have")
        if gap_data["possessed_required"]:
            for s in gap_data["possessed_required"]:
                st.markdown(f"- **{s}** *(Core Requirement)*")
        else:
            st.info("You haven't added any of this role's core skills to your profile yet.")

        if gap_data["possessed_recommended"]:
            st.markdown("##### *Recommended Skills Possessed:*")
            for s in gap_data["possessed_recommended"]:
                st.markdown(f"- {s} *(Elective Boost)*")

    with col_mis_list:
        st.markdown("### ⚠️ Skill Gaps to Close")
        if gap_data["missing_required"]:
            for s in gap_data["missing_required"]:
                st.markdown(f"- 🔴 **{s}** *(Required for {selected_role})*")
        else:
            st.success(f"🎉 Fantastic! You have mastered all baseline required skills for {selected_role}!")

        if gap_data["missing_recommended"]:
            st.markdown("##### *Recommended Skills to Learn:*")
            for s in gap_data["missing_recommended"]:
                st.markdown(f"- 🟡 {s} *(Recommended)*")

    # Bridge the Gaps - Recommended Courses for Missing Skills
    st.markdown("---")
    st.markdown("### 🎯 Recommended Courses to Close Your Skill Gaps")
    st.caption("Enroll in these targeted courses to acquire your missing skills systematically.")

    if not gap_data["missing_required"] and not gap_data["missing_recommended"]:
        st.success("No gaps remaining! Explore advanced or elective topics in the Course Catalog.")
    else:
        # Check active enrollments
        active_cids = {c["id"] for c in profile.get("active_courses", [])}
        completed_cids = {c["id"] for c in profile.get("completed_courses", [])}

        for skill, courses in gap_data["missing_skill_courses"].items():
            if not courses:
                continue
            with st.expander(f"📚 Courses teaching **{skill}** ({len(courses)} available)", expanded=True):
                for c in courses:
                    cid = c["id"]
                    col_c1, col_c2 = st.columns([4, 1])
                    with col_c1:
                        st.markdown(
                            f"**[{c['course_code']}] {c['title']}** &nbsp;•&nbsp; Level: `{c['difficulty_level']}` &nbsp;•&nbsp; Duration: `{c['estimated_duration_hours']}h`"
                        )
                    with col_c2:
                        if cid in completed_cids:
                            st.caption("✓ Completed")
                        elif cid in active_cids:
                            st.caption("📖 Enrolled")
                        else:
                            if st.button("Enroll", key=f"gap_enr_{skill}_{cid}", type="primary"):
                                if on_enroll_callback:
                                    on_enroll_callback(user_id, cid)
