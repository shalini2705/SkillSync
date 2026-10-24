"""
Personalized Recommendation Engine.
Implements TF-IDF vectorization and Cosine Similarity combined with
multi-criteria ranking:
1. Target career role alignment
2. Role skill gap closure
3. Prerequisite readiness
4. Preferred difficulty match
5. Student feedback & peer rating weighting
6. Exclusion of already completed courses
7. Explainable reasoning generation
"""

from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

from database.db import fetch_all, fetch_one
from modules.course_catalog import get_courses
from modules.student_profile import get_student_profile
from utils.helpers import get_difficulty_badge, render_stars


def build_course_document(course: Dict) -> str:
    """
    Constructs a rich textual representation of a course for TF-IDF vectorization.
    Skills and target roles are repeated to provide appropriate feature weighting.
    """
    skills_text = " ".join([f"{s} {s}" for s in course.get("skills", [])])
    roles_text = " ".join([f"{r} {r}" for r in course.get("target_roles", [])])
    prereqs_text = " ".join([p.get("title", "") for p in course.get("prerequisites", [])])

    doc = f"{course['title']} {course['title']} {course['category']} {course['difficulty_level']} {course['description']} {skills_text} {roles_text} {prereqs_text}"
    return doc


def build_student_document(profile: Dict, role_required_skills: List[str]) -> str:
    """
    Constructs a rich textual representation of the student's profile, target role,
    current skills, missing career skills, and topical interests.
    """
    target_role = profile.get("target_role", "")
    current_skills = profile.get("skills", [])
    interests = profile.get("interests", [])
    difficulty = profile.get("preferred_difficulty", "")

    # Skills the student needs for their career role that they don't have yet
    missing_target_skills = [s for s in role_required_skills if s.lower() not in [cs.lower() for cs in current_skills]]

    # Weighted text
    role_rep = f"{target_role} {target_role} {target_role}"
    missing_rep = " ".join([f"{s} {s}" for s in missing_target_skills])
    skills_rep = " ".join(current_skills)
    interests_rep = " ".join(interests)

    return f"{role_rep} {missing_rep} {skills_rep} {interests_rep} {difficulty}"


def get_recommendations(
    user_id: int,
    top_n: int = 8,
    db_path: str = None
) -> Tuple[List[Dict], Dict]:
    """
    Generates personalized, explainable course recommendations for a student.
    Returns:
        (recommended_courses_list, diagnostic_summary)
    """
    profile = get_student_profile(user_id, db_path=db_path)
    all_courses = get_courses(db_path=db_path)

    if not all_courses:
        return [], {"status": "empty_catalog", "message": "The course catalog is currently empty."}

    # Identify completed course IDs to exclude them from new recommendations
    completed_cids = {c["id"] for c in profile.get("completed_courses", [])}
    active_cids = {c["id"] for c in profile.get("active_courses", [])}

    # Fetch required skills for the student's target career role
    target_role_name = profile.get("target_role", "Data Analyst")
    role_skill_rows = fetch_all(
        """
        SELECT s.name, rs.importance
        FROM role_skills rs
        JOIN skills s ON rs.skill_id = s.id
        JOIN career_roles cr ON rs.role_id = cr.id
        WHERE cr.name = ?
        """,
        (target_role_name,),
        db_path=db_path
    )
    role_skills = [r["name"] for r in role_skill_rows]
    student_skills_set = {s.lower() for s in profile.get("skills", [])}
    missing_role_skills = [s for s in role_skills if s.lower() not in student_skills_set]

    # Student past rating preference (feedback loop):
    # Check if student gave high ratings (>=4) to specific categories
    high_rated_categories = set()
    low_rated_categories = set()
    for comp in profile.get("completed_courses", []):
        r_val = comp.get("rating")
        cat = comp.get("category")
        if r_val and cat:
            if r_val >= 4:
                high_rated_categories.add(cat)
            elif r_val <= 2:
                low_rated_categories.add(cat)

    # Filter out already completed courses
    candidate_courses = [c for c in all_courses if c["id"] not in completed_cids]

    if not candidate_courses:
        return [], {
            "status": "all_completed",
            "message": "Congratulations! You have completed all courses in the catalog for this category."
        }

    # Build Corpus for TF-IDF
    course_docs = [build_course_document(c) for c in candidate_courses]
    student_doc = build_student_document(profile, role_skills)

    # Compute TF-IDF Cosine Similarity
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    all_docs = course_docs + [student_doc]
    tfidf_matrix = vectorizer.fit_transform(all_docs)

    course_vectors = tfidf_matrix[:-1]
    student_vector = tfidf_matrix[-1:]

    cosine_sims = cosine_similarity(student_vector, course_vectors).flatten()

    # Multi-factor re-ranking
    scored_candidates = []
    preferred_diff = profile.get("preferred_difficulty", "All")

    for idx, course in enumerate(candidate_courses):
        raw_sim = float(cosine_sims[idx])

        # Factor 1: TF-IDF Base Score (0 to 45 pts)
        base_tfidf_score = raw_sim * 45.0

        # Factor 2: Direct Target Role Match (up to 20 pts)
        role_match = any(target_role_name.lower() == r.lower() for r in course.get("target_roles", []))
        role_pts = 20.0 if role_match else 0.0

        # Factor 3: Teaches Missing Skills for Target Role (up to 20 pts)
        course_skills = course.get("skills", [])
        teaches_missing = [s for s in course_skills if s.lower() in [ms.lower() for ms in missing_role_skills]]
        teaches_existing = [s for s in course_skills if s.lower() in student_skills_set]

        skill_pts = min(20.0, len(teaches_missing) * 10.0)

        # Factor 4: Preferred Difficulty Match (up to 8 pts)
        diff_pts = 0.0
        if preferred_diff == "All" or preferred_diff == course["difficulty_level"]:
            diff_pts = 8.0
        elif preferred_diff == "Beginner" and course["difficulty_level"] == "Advanced":
            diff_pts = -5.0

        # Factor 5: Prerequisite Readiness (up to 7 pts)
        # Check if student meets prerequisites
        prereqs = course.get("prerequisites", [])
        missing_prereqs = []
        for p in prereqs:
            # Check if student completed the prerequisite course
            p_code = p["course_code"]
            completed_codes = {c["course_code"] for c in profile.get("completed_courses", [])}
            if p_code not in completed_codes:
                missing_prereqs.append(p)

        prereq_pts = 7.0 if len(prereqs) == 0 or len(missing_prereqs) == 0 else -6.0

        # Factor 6: Peer Course Rating Boost (up to 5 pts)
        avg_rating = course.get("avg_rating", 0.0)
        rating_pts = (avg_rating / 5.0) * 5.0 if avg_rating > 0 else 2.5

        # Factor 7: Student Feedback Loop adjustment (+5 for high rated cat, -5 for low rated cat)
        feedback_adj = 0.0
        if course["category"] in high_rated_categories:
            feedback_adj += 5.0
        elif course["category"] in low_rated_categories:
            feedback_adj -= 5.0

        # Total combined score normalized between 5% and 98%
        total_score = base_tfidf_score + role_pts + skill_pts + diff_pts + prereq_pts + rating_pts + feedback_adj
        normalized_score = max(5.0, min(99.0, total_score))

        # Build Explainability Reason
        reasons = []
        if role_match:
            reasons.append(f"Directly prepares you for **{target_role_name}**")
        if teaches_missing:
            skills_listed = ", ".join(teaches_missing)
            reasons.append(f"Closes critical skill gaps: **{skills_listed}**")
        if teaches_existing:
            reasons.append(f"Deepens your existing knowledge in **{', '.join(teaches_existing)}**")
        if preferred_diff != "All" and preferred_diff == course["difficulty_level"]:
            reasons.append(f"Matches your **{preferred_diff}** difficulty preference")
        if len(prereqs) > 0 and len(missing_prereqs) == 0:
            reasons.append("You have completed all prerequisites")
        elif len(missing_prereqs) > 0:
            p_names = ", ".join([p["course_code"] for p in missing_prereqs])
            reasons.append(f"⚠️ Missing prerequisite: {p_names} (take foundational course first)")
        if course["category"] in high_rated_categories:
            reasons.append(f"Aligned with your positive feedback in {course['category']}")
        if avg_rating >= 4.5:
            reasons.append(f"Top community rated course ({avg_rating:.1f}/5.0)")

        if not reasons:
            reasons.append(f"Relevant foundational course in {course['category']}")

        course_copy = dict(course)
        course_copy["relevance_score"] = round(normalized_score, 1)
        course_copy["explanation"] = " • ".join(reasons)
        course_copy["teaches_missing_skills"] = teaches_missing
        course_copy["missing_prereqs"] = missing_prereqs
        course_copy["is_enrolled"] = course["id"] in active_cids

        scored_candidates.append(course_copy)

    # Sort descending by relevance score
    scored_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

    top_recs = scored_candidates[:top_n]

    diagnostics = {
        "status": "success",
        "target_role": target_role_name,
        "missing_role_skills_count": len(missing_role_skills),
        "total_catalog_evaluated": len(all_courses),
        "eligible_courses_count": len(candidate_courses),
        "completed_count": len(completed_cids)
    }

    return top_recs, diagnostics


def render_recommendations(user_id: int, on_enroll_callback = None):
    """Renders the Personalized Recommendations view with rich cards and explanations."""
    st.markdown("## 🎯 Your Personalized Course Recommendations")
    st.caption("AI-powered content matching driven by your target role, skill gaps, learning preferences, and course ratings.")

    recs, diagnostics = get_recommendations(user_id)

    if diagnostics.get("status") == "empty_catalog":
        st.warning("No courses are available in the catalog yet. Please check back later.")
        return

    if diagnostics.get("status") == "all_completed":
        st.success("🎉 Outstanding achievement! You have completed all courses available in the catalog.")
        return

    if not recs:
        st.info("No recommendations found. Please ensure your profile has a target role or skills selected.")
        return

    st.markdown(
        f"""
        <div class="alert-box alert-info">
            <strong>Target Goal:</strong> {diagnostics['target_role']} &nbsp;|&nbsp; 
            <strong>Identified Skill Gaps:</strong> {diagnostics['missing_role_skills_count']} skills to master &nbsp;|&nbsp; 
            <strong>Relevance Engine:</strong> Scikit-learn TF-IDF & Cosine Similarity + Prerequisite and Feedback Ranking
        </div>
        """,
        unsafe_allow_html=True
    )

    for course in recs:
        cid = course["id"]
        score = course["relevance_score"]
        diff_badge = get_difficulty_badge(course["difficulty_level"])
        stars_badge = render_stars(course["avg_rating"])

        with st.container():
            st.markdown(
                f"""
                <div class="rec-card">
                    <div class="rec-header">
                        <div>
                            <span class="rec-score-badge">⚡ {score}% Relevance Match</span>
                            <span style="margin-left: 0.5rem;">{diff_badge}</span>
                        </div>
                        <div>
                            <span style="color:#D97706; font-size:0.9rem; font-weight:600;">{stars_badge}</span>
                        </div>
                    </div>
                    <h3 class="rec-title">[{course['course_code']}] {course['title']}</h3>
                    <div style="font-size:0.88rem; color:#64748B; margin-top:0.25rem;">
                        <strong>Category:</strong> {course['category']} &nbsp;•&nbsp; 
                        <strong>Estimated Duration:</strong> {course['estimated_duration_hours']} hours
                    </div>
                    <p style="font-size:0.92rem; color:#334155; margin:0.75rem 0 0.5rem 0;">
                        {course['description']}
                    </p>
                    <div class="reason-box">
                        💡 <strong>Why Recommended:</strong> {course['explanation']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Skills and enrollment action row
            col_sk, col_btn = st.columns([4, 1])
            with col_sk:
                skills_tags = " ".join([f'<span class="skill-tag">🏷️ {s}</span>' for s in course["skills"]])
                st.markdown(f"**Skills Taught:** {skills_tags}", unsafe_allow_html=True)
                if course["missing_prereqs"]:
                    p_codes = ", ".join([p["course_code"] for p in course["missing_prereqs"]])
                    st.warning(f"Note: This course builds on prerequisite knowledge from: {p_codes}")

            with col_btn:
                if course.get("is_enrolled"):
                    st.button("✓ Enrolled", key=f"rec_enrolled_{cid}", disabled=True, use_container_width=True)
                else:
                    if st.button("🚀 Enroll Now", key=f"rec_enroll_{cid}", type="primary", use_container_width=True):
                        if on_enroll_callback:
                            on_enroll_callback(user_id, cid)

            st.markdown("<br/>", unsafe_allow_html=True)
