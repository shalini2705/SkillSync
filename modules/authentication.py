"""
Authentication module handling password hashing, registration,
login validation, session management, and role-based access control.
"""

from typing import Tuple, Optional, Dict
from werkzeug.security import generate_password_hash, check_password_hash
import streamlit as st

from database.db import fetch_one, execute_insert
from utils.validators import validate_registration


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Werkzeug's secure pbkdf2:sha256 algorithm."""
    return generate_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored hash."""
    return check_password_hash(hashed_password, plain_password)


def register_user(
    name: str,
    email: str,
    password: str,
    confirm_password: str,
    role: str = "student",
    db_path: str = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Validates input, checks for duplicate email, hashes the password,
    and inserts a new user record.
    """
    is_valid, err_msg = validate_registration(name, email, password, confirm_password)
    if not is_valid:
        return False, err_msg, None

    clean_email = email.strip().lower()
    clean_name = name.strip()

    # Check for duplicate email
    existing_user = fetch_one("SELECT id FROM users WHERE email = ?", (clean_email,), db_path=db_path)
    if existing_user:
        return False, f"An account with email '{clean_email}' already exists. Please log in.", None

    hashed = hash_password(password)

    try:
        user_id = execute_insert(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (clean_name, clean_email, hashed, role),
            db_path=db_path
        )

        # If student, create an empty default student profile
        if role == "student":
            execute_insert(
                "INSERT INTO student_profiles (user_id, target_role, preferred_difficulty, weekly_study_hours) VALUES (?, 'Data Analyst', 'All', 10)",
                (user_id,),
                db_path=db_path
            )

        return True, "Registration successful! You can now log in.", user_id
    except Exception as e:
        return False, f"Registration failed due to a system error: {str(e)}", None


def authenticate_user(email: str, password: str, db_path: str = None) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validates login credentials.
    Returns (success, message, user_dict).
    """
    if not email or not password:
        return False, "Please enter both email and password.", None

    clean_email = email.strip().lower()
    user = fetch_one("SELECT id, full_name, email, password_hash, role FROM users WHERE email = ?", (clean_email,), db_path=db_path)

    if not user:
        return False, "Invalid email or password.", None

    if not verify_password(password, user["password_hash"]):
        return False, "Invalid email or password.", None

    # Don't return password hash in session user object
    user_data = {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"]
    }
    return True, "Login successful!", user_data


def init_session_state():
    """Initializes authentication keys in Streamlit session state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


def login_session(user_dict: dict):
    """Sets session state to logged in with the user details."""
    st.session_state.authenticated = True
    st.session_state.user = user_dict


def logout_session():
    """Clears authentication session state."""
    st.session_state.authenticated = False
    st.session_state.user = None


def is_authenticated() -> bool:
    """Checks if a user is currently authenticated."""
    return st.session_state.get("authenticated", False) and st.session_state.get("user") is not None


def is_admin() -> bool:
    """Checks if the logged-in user has the admin role."""
    return is_authenticated() and st.session_state.user.get("role") == "admin"


def get_current_user() -> Optional[Dict]:
    """Returns the current user dict from session state."""
    return st.session_state.get("user")


def render_auth_page():
    """Renders the Login and Registration UI tabs."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #1E3A8A; font-weight: 800;">Welcome to SkillSync</h2>
            <p style="color: #64748B;">Empowering students with tailored learning paths and role-aligned course recommendations</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

    with tab_login:
        st.subheader("Sign In to Your Account")
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email Address", placeholder="e.g., student@codegnan.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Sign In", use_container_width=True)

            if submit_login:
                success, msg, user_data = authenticate_user(email, password)
                if success:
                    login_session(user_data)
                    st.success(f"Welcome back, {user_data['full_name']}!")
                    st.rerun()
                else:
                    st.error(msg)

        # Quick demo login hint for hackathon judges
        with st.expander("ℹ️ Hackathon Quick-Login Credentials"):
            st.markdown(
                """
                **Sample Student Account:**  
                - **Email:** `student@codegnan.com`  
                - **Password:** `StudentPass2026!`  

                **Administrator Account:**  
                - **Email:** `admin@codegnan.com`  
                - **Password:** `AdminSecurePass2026!`  
                *(Or register any new student account using the Create Account tab)*
                """
            )

    with tab_register:
        st.subheader("Student Registration")
        st.caption("Join our learning platform to uncover your career skill gaps and receive custom course recommendations.")
        with st.form("register_form", clear_on_submit=True):
            name = st.text_input("Full Name", placeholder="e.g., Priya Sharma")
            reg_email = st.text_input("Email Address", placeholder="e.g., priya.s@example.com")
            reg_password = st.text_input("Create Password (min. 6 characters)", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_register = st.form_submit_button("Create My Account", use_container_width=True)

            if submit_register:
                success, msg, _ = register_user(name, reg_email, reg_password, confirm_password, role="student")
                if success:
                    st.success(msg)
                    st.info("You can now switch to the 'Sign In' tab to log in with your new credentials.")
                else:
                    st.error(msg)
