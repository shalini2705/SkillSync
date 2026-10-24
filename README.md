# 🎓 SkillSync — Personalized Course Recommendation System
### Codegnan AI Avengers Hackathon 2026
**Domain:** Artificial Intelligence in Education & Career Development  
**Tech Stack:** Python 3.12, Streamlit, SQLite, Scikit-learn, Pandas, NumPy, Plotly, Werkzeug  

---

## 📌 1. Problem Statement
When college students select elective courses or technical certifications, they often rely on peer suggestions rather than an objective analysis of their current skills, career aspirations, and prerequisite readiness. This leads to:
- Disconnected learning paths and redundant coursework.
- Major skill gaps when applying for specific job roles (e.g., Data Analyst, ML Engineer, Web Developer).
- Frustration and reduced employment readiness upon graduation.

---

## 🎯 2. Project Objectives
Our solution provides an end-to-end web platform that:
1. **Profiles Students:** Captures current technical skills, topical interests, completed courses, preferred difficulty, and weekly study hours.
2. **Recommends Tailored Courses:** Uses **Scikit-learn TF-IDF Vectorization and Cosine Similarity** combined with role-skill matching to recommend the most relevant courses.
3. **Explains Every Recommendation:** Transparently provides the rationale behind each suggestion (e.g., *"Closes critical skill gaps in SQL and Excel for Data Analyst"*).
4. **Calculates Skill Gaps:** Computes the mathematical readiness percentage against industry roles and lists courses to bridge missing competencies.
5. **Generates Prerequisite-Aware Learning Roadmaps:** Sorts courses topologically to ensure foundations are mastered before advanced topics, estimating study weeks based on personal pace.
6. **Enforces a Continuous Feedback Loop:** Allows students to mark courses as completed, submit 1–5 star ratings and reviews, which dynamically refines future recommendation ranking.
7. **Empowers Administrators:** Provides real-time enrollment analytics, course distribution charts, role-skill matrix management, and complete course CRUD operations.

---

## 🏛️ 3. Architecture & Tech Stack

```
   ┌────────────────────────────────────────────────────────────┐
   │             Streamlit Web Frontend (app.py)               │
   │   (Blue & White Modern UI, Custom CSS, Plotly Charts)      │
   └─────────────┬────────────────────────────────┬─────────────┘
                 │                                │
                 ▼                                ▼
   ┌───────────────────────────┐    ┌───────────────────────────┐
   │    Machine Learning       │    │    Business Logic & Auth  │
   │  Recommendation Engine    │    │  (Role-Based Access,      │
   │  - Scikit-learn TF-IDF    │    │   Enrollments, Roadmaps,  │
   │  - Cosine Similarity      │    │   Skill-Gap Analyzer)     │
   │  - Multi-Factor Re-rank   │    └─────────────┬─────────────┘
   └─────────────┬─────────────┘                  │
                 │                                │
                 ▼                                ▼
   ┌────────────────────────────────────────────────────────────┐
   │               SQLite Relational Database                   │
   │  (Users, Profiles, Courses, Skills, Roles, Enrollments)   │
   └────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend UI** | Streamlit + Custom CSS | Clean, responsive web dashboard with sidebar navigation |
| **Programming Language** | Python 3.12 | Core backend application logic |
| **Database** | SQLite3 | Relational data persistence with foreign keys and cascading |
| **Data Processing** | Pandas, NumPy | Structured data manipulation and vector computations |
| **Machine Learning** | Scikit-learn | TF-IDF text vectorization and Cosine Similarity matching |
| **Visualizations** | Plotly Graph Objects / Express | Skill readiness gauges, enrollment comparisons, category donuts |
| **Security** | Werkzeug Security | PBKDF2:SHA256 password hashing and role-based session control |
| **Testing** | Pytest | 20 automated unit tests verifying core requirements |

---

## 🗄️ 4. Database Schema Design

The database (`database/course_recommender.db`) is structured with 3NF-compliant relational tables:

1. **`users`**: User authentication records (`id`, `full_name`, `email` [UNIQUE], `password_hash`, `role` ['student'/'admin']).
2. **`student_profiles`**: Student learning preferences (`target_role`, `preferred_difficulty`, `weekly_study_hours`, `updated_at`).
3. **`skills`**: Standard skills repository (`name`, `category`).
4. **`career_roles`**: Supported job pathways (`name`, `description`).
5. **`role_skills`**: Mapping of required vs recommended skills per career role.
6. **`student_skills`**: Current skills possessed by each student.
7. **`student_interests`**: Topical interests selected by students.
8. **`courses`**: Course catalog (`course_code` [UNIQUE], `title`, `description`, `category`, `difficulty_level`, `estimated_duration_hours`).
9. **`course_skills`**: Skills taught by each course.
10. **`course_prerequisites`**: Direct prerequisite course mappings for topological sequencing.
11. **`course_target_roles`**: Direct alignment between courses and career paths.
12. **`enrollments`**: Course enrollment lifecycle (`status` in ['Enrolled', 'In Progress', 'Completed'], `enrolled_at`, `completed_at`).
13. **`ratings`**: Star ratings (1-5) and written reviews submitted by students upon completion.

---

## 🧠 5. How the Recommendation Engine Works

The recommendation engine (`modules/recommendation_engine.py`) uses a two-stage hybrid approach:

### Stage 1: TF-IDF Text Representation & Cosine Similarity
1. **Course Documents:** Combines course title, description, category, difficulty, skills taught, target roles, and prerequisites into a single feature document.
2. **Student Profile Document:** Combines the student's target career role (triply weighted), missing required skills for that role (doubly weighted), current skills, topical interests, and preferred difficulty.
3. **Vectorization:** `TfidfVectorizer(ngram_range=(1,2), stop_words='english')` converts textual documents into sparse mathematical vectors.
4. **Cosine Similarity:** Measures the angle between the student's profile vector and every course vector in $N$-dimensional space:
   $$\text{Cosine Similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$$

### Stage 2: Multi-Factor Re-ranking Formula
Raw similarity is calibrated into an explainable **Relevance Match Score (5% – 99%)**:
- **Base TF-IDF Similarity:** Up to 45 points.
- **Target Role Direct Match:** $+20$ points if the course is explicitly tailored for the student's chosen career role.
- **Missing Skill Gap Closure:** $+10$ points per missing career skill taught by the course (up to $+20$ points).
- **Preferred Difficulty Alignment:** $+8$ points if difficulty matches student preference (penalty if Advanced when Beginner requested).
- **Prerequisite Readiness:** $+7$ points if student meets all prerequisites ($-6$ points if missing prerequisites, accompanied by a clear warning).
- **Peer Course Rating:** Up to $+5$ points based on platform average rating.
- **Student Feedback Adjustment:** $+5$ points if the student previously gave $\ge 4$ stars to courses in this category; $-5$ points if $\le 2$ stars.
- **Exclusion Filter:** Already completed courses are **strictly excluded** from new recommendations.

---

## 📂 6. Project Folder Structure

```
da hackanon/
│
├── app.py                      # Main Streamlit application entrypoint
├── requirements.txt            # Project Python dependencies
├── README.md                   # Comprehensive documentation and hackathon guide
├── .gitignore                  # Git ignore rules
├── .env.example                # Sample environment variables
│
├── database/                   # Database subsystem
│   ├── __init__.py
│   ├── db.py                   # SQLite connection helpers & queries
│   ├── schema.sql              # Relational SQL schema
│   ├── seed_data.py            # Automatic seeder with 22 courses & sample users
│   └── course_recommender.db   # Local SQLite database file
│
├── modules/                    # Application feature modules
│   ├── __init__.py
│   ├── authentication.py       # Password hashing, registration & login
│   ├── student_profile.py      # Profile editing & skill preferences
│   ├── course_catalog.py       # Course catalog search, filter & sorting
│   ├── recommendation_engine.py# Scikit-learn TF-IDF recommender
│   ├── skill_gap_analysis.py   # Skill gap metrics & Plotly charts
│   ├── learning_path.py        # Prerequisite-aware roadmap generator
│   ├── enrollment.py           # Enrollment lifecycle management
│   ├── feedback.py             # Course ratings & feedback loop
│   └── admin_dashboard.py      # Admin analytics & Course CRUD
│
├── utils/                      # Helper utilities
│   ├── __init__.py
│   ├── validators.py           # Form and input validation routines
│   └── helpers.py              # CSS styles, badges & visual formatters
│
└── tests/                      # Automated test suite
    ├── __init__.py
    ├── test_database.py        # DB schema & seed verification
    ├── test_auth.py            # Password hashing & registration tests
    ├── test_course_catalog.py  # Course retrieval & filter tests
    ├── test_recommendations.py # Recommender ranking & exclusion tests
    ├── test_skill_gap.py       # Skill gap percentage calculation tests
    ├── test_learning_path.py   # Prerequisite sequence ordering tests
    ├── test_enrollment_feedback.py # Status progression & rating tests
    └── test_admin.py           # Admin Course CRUD & metrics tests
```

---

## ⚡ 7. Installation and Local Setup

Follow these exact steps in **Windows PowerShell**:

### Step 1: Open Terminal in Project Directory
```powershell
cd "c:\Users\pamul\OneDrive\Desktop\da hackanon"
```

### Step 2: Create and Activate Virtual Environment (Optional but Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Initialize and Seed the Database
```powershell
python -m database.seed_data
```
*(This automatically creates the schema and populates 22 sample courses, skills, and initial accounts without duplication).*

### Step 5: Start the Streamlit Application
```powershell
streamlit run app.py
```
Streamlit will automatically launch in your default browser at `http://localhost:8501`.

---

## 🧪 8. Running Automated Tests

Run the full pytest suite with verbose output:
```powershell
python -m pytest -v
```

All **20 tests** should pass:
- Database initialization and table constraints.
- User registration and duplicate email rejection.
- Password hashing and login verification.
- Course creation, filtering, and deletion.
- Recommendation score ranking and explainability.
- Exclusion of completed courses from recommendations.
- Profile-specific recommendations (Data Analyst vs Web Developer).
- Mathematical skill-gap percentage calculation.
- Prerequisite-aware learning path topological sorting.
- Enrollment duplicate prevention.
- Course completion requirement before submitting ratings.
- Administrator course CRUD and platform analytics.

---

## 🔑 9. Demo Credentials

For quick evaluation during the hackathon demonstration:

| Role | Email | Password |
|---|---|---|
| **Student (Pre-configured)** | `student@codegnan.com` | `StudentPass2026!` |
| **Administrator** | `admin@codegnan.com` | `AdminSecurePass2026!` |

*You can also click **"Create Account"** to register any new student account on the fly.*

---

## 🏆 10. Live Hackathon Demonstration Script (11 Steps)

Follow this step-by-step walkthrough to present the project to judges:

1. **Step 1: Open Landing Page**  
   Start at `http://localhost:8501`. Highlight the problem statement (students picking courses blindly) and the hero overview.
2. **Step 2: Sign In as Student**  
   Navigate to **Sign In** and log in with `student@codegnan.com` / `StudentPass2026!`.
3. **Step 3: Show Student Profile**  
   Open **Student Profile**. Show target role (`Data Analyst`), current skills (`Excel`, `Python`), and study hours (12 hrs/week).
4. **Step 4: Generate Personalized Recommendations**  
   Click **My Recommendations**. Show how top courses like `SQL Fundamentals`, `Statistics`, and `Data Wrangling with Pandas` appear at the top.
5. **Step 5: Explain Recommendation Reasons**  
   Point to the explanation box on the cards: *"Directly prepares you for Data Analyst • Closes critical skill gaps: SQL • Matches your Intermediate difficulty preference"*.
6. **Step 6: Open Skill-Gap Analysis**  
   Click **Skill-Gap Analysis**. Show the Plotly Gauge Chart and the Required Skills Breakdown. Explain that the student has 2 out of 6 core skills, resulting in a **33.3% Readiness Score**. Show the courses recommended for the missing skills.
7. **Step 7: View Learning Roadmap**  
   Click **Learning Roadmap**. Point out how foundational courses (Step 1) appear before advanced courses (Step 2 and Step 3). Show the timeline: ~7.6 weeks at 12 hours/week.
8. **Step 8: Enroll in a Course**  
   Click **Enroll** on `SQL Fundamentals for Relational Databases`.
9. **Step 9: Complete and Rate Course**  
   Go to **My Enrollments**, click **Mark Completed** on `SQL Fundamentals`, and give it a **5-star rating** with feedback.
10. **Step 10: Observe Feedback & Exclusion Effect**  
    Go back to **My Recommendations**. Notice that `SQL Fundamentals` is now **excluded** from new recommendations because it is completed, and subsequent courses like `Advanced SQL` now appear with higher relevance!
11. **Step 11: Switch to Admin Dashboard**  
    Sign out, log in as `admin@codegnan.com` / `AdminSecurePass2026!`, and open **Admin Dashboard**. Show the live Plotly analytics: Most Enrolled Courses, Top Rated Courses, Category Distribution, and Catalog Skill-Coverage by role. Demonstrate the **Add Course** form.

---

## ☁️ 11. Cloud Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub (ensure `.gitignore` excludes `.venv`, `.pytest_cache`, and temporary files).
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
3. Select this repository and branch `main`.
4. Set main file path to: `app.py`.
5. Under **Advanced Settings > Secrets**, configure:
   ```toml
   ADMIN_EMAIL = "admin@codegnan.com"
   ADMIN_PASSWORD = "AdminSecurePass2026!"
   ```
6. Click **Deploy!**

> **Note on SQLite in Cloud Containers:** Streamlit Community Cloud uses ephemeral container instances. While SQLite works perfectly for demonstrations and local execution, for multi-tenant production deployments with permanent data persistence across restarts, migrate the connection in `database/db.py` to a hosted PostgreSQL database (e.g., Supabase or Neon).

---

## 🔮 12. Future Enhancements
- **Collaborative Filtering:** As student enrollments and ratings scale into thousands, incorporate Matrix Factorization (SVD / ALS) to recommend courses based on similar peer cohorts.
- **Resume Skill Extractor:** Allow students to upload a PDF resume, using NLP entity extraction (SpaCy) to automatically populate their current skills.
- **Certificate Verification:** Generate downloadable completion certificates with cryptographic verification hashes.

---

*Engineered with ❤️ for the Codegnan AI Avengers Hackathon 2026.*
