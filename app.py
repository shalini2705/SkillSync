"""
Personalized Course Recommendation System
Codegnan AI Avengers Hackathon

Main Streamlit Application Controller.
Coordinates authentication, student profiling, recommendation engine,
skill-gap analysis, learning path roadmap, enrollment lifecycle, and admin analytics.
"""

import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="AI Avengers - Course Recommender",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Database Auto-Initialization
from database.seed_data import seed_database
from utils.helpers import load_custom_css
from modules.authentication import (
    init_session_state,
    is_authenticated,
    is_admin,
    get_current_user,
    logout_session,
    render_auth_page
)
from modules.student_profile import render_student_profile
from modules.course_catalog import render_course_catalog
from modules.recommendation_engine import render_recommendations
from modules.skill_gap_analysis import render_skill_gap_page
from modules.learning_path import render_learning_path_page
from modules.enrollment import enroll_course
from modules.feedback import render_my_enrollments_page
from modules.admin_dashboard import render_admin_dashboard

# Ensure database is initialized and seeded on app startup
seed_database()

# Inject styling
load_custom_css()
init_session_state()


def handle_course_enrollment(user_id: int, course_id: int):
    """Global callback for enrolling in a course from any view."""
    success, msg = enroll_course(user_id, course_id)
    if success:
        st.toast("🎉 Enrolled successfully!", icon="✅")
        st.success(msg)
        st.rerun()
    else:
        st.toast(msg, icon="⚠️")
        st.warning(msg)


def render_landing_page():
    """Renders an engaging home / landing page explaining the platform."""
    st.markdown(
        """
        <div class="hero-banner">
            <h1>🎓 Personalized Course Recommendation System</h1>
            <p>Codegnan AI Avengers Hackathon Project &nbsp;|&nbsp; Smart Learning Path & Skill-Gap Optimization</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(
            """
            ### 💡 The Problem We Solve
            Students often pick elective courses or technical certifications based on peer suggestions rather than their personal strengths, missing skills, and career goals. This results in disjointed learning journeys, wasted time, and poor job readiness.

            ### 🚀 Our Intelligent Solution
            Our recommendation platform combines **Machine Learning (TF-IDF Vectorization & Cosine Similarity)** with **Role-Skill Gap Modeling** to curate a bespoke learning path for every student:
            - **Target Career Alignment:** Direct mapping to industry positions such as *Data Analyst*, *Machine Learning Engineer*, *Data Engineer*, and *Python Developer*.
            - **Prerequisite-Aware Sequences:** Never suggests advanced deep learning before foundational Python and statistics.
            - **Explainable Recommendations:** Transparently reveals *why* each course was chosen and which skill gaps it eliminates.
            - **Continuous Feedback Loop:** Uses course ratings and completion data to continuously optimize suggestions.
            """
        )

        st.markdown("<br/>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Sign In / Register", type="primary", use_container_width=True):
                st.session_state["active_nav"] = "🔑 Sign In / Register"
                st.rerun()
        with col_btn2:
            if st.button("📚 Browse Course Catalog", use_container_width=True):
                st.session_state["active_nav"] = "📚 Course Catalog"
                st.rerun()

    with col2:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:1.5rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
                <h4 style="color:#1E3A8A; margin-top:0;">⚡ Live Demonstration Workflow</h4>
                <ol style="color:#334155; font-size:0.92rem; line-height:1.7; padding-left:1.2rem;">
                    <li><strong>Sign In:</strong> Log in with sample credentials or register a new student account.</li>
                    <li><strong>Build Profile:</strong> Select your technical skills, interests, and target career role.</li>
                    <li><strong>AI Recommendations:</strong> View ranked courses with explainable matching reasons.</li>
                    <li><strong>Skill-Gap Analysis:</strong> Visualize your role readiness percentage and missing competencies.</li>
                    <li><strong>Learning Roadmap:</strong> Follow an ordered sequence with estimated study timelines.</li>
                    <li><strong>Enroll & Rate:</strong> Mark courses completed and submit feedback to refine the recommender.</li>
                    <li><strong>Admin Portal:</strong> Explore platform analytics, catalog coverage, and course CRUD.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True
        )


def main():
    # Sidebar Branding
    st.sidebar.markdown(
        """
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <h2 style="color:#1E3A8A; font-weight:800; margin:0;">AI AVENGERS</h2>
            <p style="color:#64748B; font-size:0.85rem; margin:0;">Codegnan Hackathon 2026</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    user = get_current_user()

    # User Profile card in sidebar
    if is_authenticated():
        role_badge = "🛡️ Administrator" if is_admin() else "🎓 Student"
        st.sidebar.markdown(
            f"""
            <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:0.75rem; margin-bottom:1rem;">
                <div style="font-weight:700; color:#1E3A8A;">{user['full_name']}</div>
                <div style="font-size:0.82rem; color:#475569;">{user['email']}</div>
                <div style="font-size:0.82rem; font-weight:600; color:#2563EB; margin-top:0.25rem;">{role_badge}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Navigation Options for Logged-In Users
        if is_admin():
            nav_options = [
                "🛡️ Admin Dashboard",
                "📚 Course Catalog",
                "🚪 Sign Out"
            ]
        else:
            nav_options = [
                "🎯 My Recommendations",
                "📊 Skill-Gap Analysis",
                "🗺️ Learning Roadmap",
                "🎓 My Enrollments",
                "👤 Student Profile",
                "📚 Course Catalog",
                "🚪 Sign Out"
            ]
    else:
        # Public Navigation Options
        nav_options = [
            "🏠 Home",
            "📚 Course Catalog",
            "🔑 Sign In / Register"
        ]

    # Handle navigation state
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = nav_options[0]

    # Sync state if option no longer valid (e.g. on role change)
    if st.session_state["active_nav"] not in nav_options:
        st.session_state["active_nav"] = nav_options[0]

    selected_nav = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state["active_nav"])
    )
    st.session_state["active_nav"] = selected_nav

    # Handle Sign Out
    if selected_nav == "🚪 Sign Out":
        logout_session()
        st.session_state["active_nav"] = "🏠 Home"
        st.rerun()

    # Render Active Screen
    if selected_nav == "🏠 Home":
        render_landing_page()

    elif selected_nav == "🔑 Sign In / Register":
        render_auth_page()

    elif selected_nav == "📚 Course Catalog":
        user_id = user["id"] if is_authenticated() else None
        render_course_catalog(user_id=user_id, on_enroll_callback=handle_course_enrollment)

    elif selected_nav == "🎯 My Recommendations":
        if is_authenticated():
            render_recommendations(user["id"], on_enroll_callback=handle_course_enrollment)
        else:
            st.warning("Please sign in to view your personalized recommendations.")

    elif selected_nav == "📊 Skill-Gap Analysis":
        if is_authenticated():
            render_skill_gap_page(user["id"], on_enroll_callback=handle_course_enrollment)
        else:
            st.warning("Please sign in to view your skill-gap analysis.")

    elif selected_nav == "🗺️ Learning Roadmap":
        if is_authenticated():
            render_learning_path_page(user["id"], on_enroll_callback=handle_course_enrollment)
        else:
            st.warning("Please sign in to view your learning roadmap.")

    elif selected_nav == "🎓 My Enrollments":
        if is_authenticated():
            render_my_enrollments_page(user["id"])
        else:
            st.warning("Please sign in to view your enrollments.")

    elif selected_nav == "👤 Student Profile":
        if is_authenticated():
            render_student_profile(user["id"])
        else:
            st.warning("Please sign in to view and edit your profile.")

    elif selected_nav == "🛡️ Admin Dashboard":
        if is_admin():
            render_admin_dashboard()
        else:
            st.error("Access denied. This section is restricted to platform administrators.")

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="font-size:0.75rem; color:#94A3B8; text-align:center;">
            Codegnan AI Avengers Hackathon<br/>
            Engineered with Streamlit & Scikit-learn
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
