"""
Personalized Learning Path Generation module.
Constructs a topologically sorted, prerequisite-aware course sequence
tailored to the student's target career role, missing skills, and weekly study pace.
"""

from typing import List, Dict, Tuple
from collections import defaultdict, deque
import streamlit as st

from database.db import fetch_all
from modules.course_catalog import get_courses
from modules.student_profile import get_student_profile
from utils.helpers import get_difficulty_badge


def build_learning_path(user_id: int, db_path: str = None) -> Dict:
    """
    Generates an ordered, prerequisite-compliant learning path for the student.
    Returns:
        dict containing ordered steps, total duration, estimated weeks, and stats.
    """
    profile = get_student_profile(user_id, db_path=db_path)
    target_role = profile.get("target_role", "Data Analyst")
    weekly_hours = max(2, profile.get("weekly_study_hours", 10))
    completed_cids = {c["id"] for c in profile.get("completed_courses", [])}
    active_cids = {c["id"] for c in profile.get("active_courses", [])}

    # Fetch required skills for target role
    role_skill_rows = fetch_all(
        """
        SELECT s.name 
        FROM role_skills rs
        JOIN skills s ON rs.skill_id = s.id
        JOIN career_roles cr ON rs.role_id = cr.id
        WHERE cr.name = ?
        """,
        (target_role,),
        db_path=db_path
    )
    role_skills = {r["name"].lower() for r in role_skill_rows}

    # Fetch all candidate courses mapped to this target role or teaching target role skills
    all_courses = get_courses(db_path=db_path)
    role_relevant_courses = []

    for c in all_courses:
        # Check if course targets this role or teaches any required skills
        targets_role = any(target_role.lower() == tr.lower() for tr in c.get("target_roles", []))
        teaches_role_skill = any(s.lower() in role_skills for s in c.get("skills", []))

        if targets_role or teaches_role_skill:
            role_relevant_courses.append(c)

    # Exclude already completed courses from new path steps
    uncompleted_courses = [c for c in role_relevant_courses if c["id"] not in completed_cids]

    if not uncompleted_courses:
        return {
            "target_role": target_role,
            "steps": [],
            "total_hours": 0,
            "estimated_weeks": 0,
            "weekly_hours": weekly_hours,
            "status": "completed_all"
        }

    # Dependency Resolution / Topological Ordering
    # Map course id -> course object
    course_map = {c["id"]: c for c in all_courses}
    candidate_id_set = {c["id"] for c in uncompleted_courses}

    # Expand candidate set to include all uncompleted prerequisites recursively
    expanded = True
    while expanded:
        expanded = False
        for cid in list(candidate_id_set):
            c = course_map.get(cid)
            if not c:
                continue
            for p in c.get("prerequisites", []):
                prereq_cid = p.get("id")
                if prereq_cid and prereq_cid not in completed_cids and prereq_cid not in candidate_id_set:
                    candidate_id_set.add(prereq_cid)
                    expanded = True

    # Graph representation
    # in_degree: number of unfulfilled prerequisites within the candidate set
    # adj_list: prereq_id -> list of dependent course_ids
    in_degree = {cid: 0 for cid in candidate_id_set}
    adj_list = defaultdict(list)

    for cid in candidate_id_set:
        c = course_map[cid]
        for p in c.get("prerequisites", []):
            prereq_cid = p.get("id")
            if prereq_cid and prereq_cid in candidate_id_set:
                in_degree[cid] += 1
                adj_list[prereq_cid].append(cid)

    # Queue of courses with 0 unfulfilled prerequisites
    # Priority sorting helper: Beginner first, then Intermediate, then Advanced
    diff_order = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}

    ready_queue = [cid for cid, deg in in_degree.items() if deg == 0]
    ready_queue.sort(key=lambda cid: diff_order.get(course_map[cid]["difficulty_level"], 2))

    ordered_cids = []
    processed_set = set()

    queue = deque(ready_queue)
    while queue:
        curr_id = queue.popleft()
        if curr_id in processed_set:
            continue
        processed_set.add(curr_id)
        ordered_cids.append(curr_id)

        # Release dependencies
        for dependent_id in adj_list[curr_id]:
            in_degree[dependent_id] -= 1
            if in_degree[dependent_id] == 0:
                queue.append(dependent_id)

    # If there are any remaining courses (e.g. in case of cycle or missing link), append by difficulty
    remaining = [cid for cid in candidate_id_set if cid not in processed_set]
    remaining.sort(key=lambda cid: diff_order.get(course_map[cid]["difficulty_level"], 2))
    ordered_cids.extend(remaining)

    # Format step items with metadata
    steps = []
    total_hours = 0

    for idx, cid in enumerate(ordered_cids, start=1):
        c = course_map[cid]
        total_hours += c["estimated_duration_hours"]

        # Reason for position
        reasons = []
        if idx == 1:
            reasons.append("Foundational starting point with zero outstanding prerequisites")
        elif c.get("prerequisites"):
            p_codes = ", ".join([p["course_code"] for p in c["prerequisites"]])
            reasons.append(f"Builds directly on prerequisites: {p_codes}")
        else:
            reasons.append(f"Sequential progression for {c['difficulty_level']} competency")

        status = "Enrolled" if cid in active_cids else "Recommended"

        steps.append({
            "step_number": idx,
            "course_id": cid,
            "course_code": c["course_code"],
            "title": c["title"],
            "category": c["category"],
            "difficulty_level": c["difficulty_level"],
            "duration_hours": c["estimated_duration_hours"],
            "skills": c.get("skills", []),
            "reason": " • ".join(reasons),
            "status": status,
            "is_enrolled": cid in active_cids
        })

    estimated_weeks = round(total_hours / weekly_hours, 1) if weekly_hours > 0 else 0

    return {
        "target_role": target_role,
        "steps": steps,
        "total_hours": total_hours,
        "estimated_weeks": estimated_weeks,
        "weekly_hours": weekly_hours,
        "status": "ready"
    }


def render_learning_path_page(user_id: int, on_enroll_callback = None):
    """Renders the step-by-step learning roadmap and estimated timeline."""
    st.markdown("## 🗺️ Personalized Learning Roadmap")
    st.caption("A structured, prerequisite-aware sequence designed to guide you from your current level to job-readiness.")

    path_data = build_learning_path(user_id)

    if path_data["status"] == "completed_all":
        st.success(f"🎉 You have completed all foundational and advanced courses for {path_data['target_role']}! Review your certificates in your profile.")
        return

    steps = path_data["steps"]
    if not steps:
        st.info("No courses found for this learning track. Adjust your target role in the Student Profile.")
        return

    # Top metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Milestone Steps</div>
                <div class="metric-value">{len(steps)} Courses</div>
                <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">Target: {path_data['target_role']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color:#3B82F6;">
                <div class="metric-title">Total Study Time</div>
                <div class="metric-value">{path_data['total_hours']} Hours</div>
                <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">At {path_data['weekly_hours']} hrs/week pace</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color:#10B981;">
                <div class="metric-title">Estimated Timeline</div>
                <div class="metric-value">~{path_data['estimated_weeks']} Weeks</div>
                <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">To job-ready completion</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("### 🪜 Sequential Course Progression")
    st.info("Courses are strictly ordered so that fundamental concepts and required prerequisites are mastered before advanced topics.")

    # Timeline / Steps Card View
    for step in steps:
        step_num = step["step_number"]
        cid = step["course_id"]
        diff_badge = get_difficulty_badge(step["difficulty_level"])
        status_color = "#10B981" if step["is_enrolled"] else "#3B82F6"

        with st.container():
            col_icon, col_content, col_act = st.columns([1, 6, 2])

            with col_icon:
                st.markdown(
                    f"""
                    <div style="width:48px; height:48px; border-radius:50%; background:{status_color}; color:white; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1.2rem; margin-top:0.5rem;">
                        {step_num}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_content:
                st.markdown(
                    f"""
                    <h4 style="margin:0.25rem 0; color:#1E3A8A;">[{step['course_code']}] {step['title']}</h4>
                    <div style="font-size:0.88rem; color:#475569; margin-bottom:0.4rem;">
                        {diff_badge} &nbsp;•&nbsp; 
                        <strong>Category:</strong> {step['category']} &nbsp;•&nbsp; 
                        <strong>Duration:</strong> {step['duration_hours']} hrs
                    </div>
                    <div style="background:#F8FAFC; border-left:3px solid #60A5FA; padding:0.4rem 0.75rem; border-radius:4px; font-size:0.88rem; color:#334155; margin-bottom:0.4rem;">
                        📍 <em>{step['reason']}</em>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                skills_str = " ".join([f'<span class="skill-tag">🏷️ {s}</span>' for s in step["skills"]])
                st.markdown(skills_str, unsafe_allow_html=True)

            with col_act:
                st.write("")
                if step["is_enrolled"]:
                    st.button("✓ Enrolled", key=f"lp_enr_{cid}_{step_num}", disabled=True, use_container_width=True)
                else:
                    if st.button("🚀 Enroll", key=f"lp_btn_{cid}_{step_num}", type="primary", use_container_width=True):
                        if on_enroll_callback:
                            on_enroll_callback(user_id, cid)

            st.markdown("<hr style='margin:1rem 0; border:0; border-top:1px dashed #CBD5E1;'/>", unsafe_allow_html=True)
