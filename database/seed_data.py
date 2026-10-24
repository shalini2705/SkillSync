"""
Seed data module for initializing the database with:
- System skills
- Career roles and their required/recommended skills
- Comprehensive sample course catalog (22 courses covering all tracks)
- Course prerequisites and role mappings
- Default Administrator account
- Sample student with baseline profile, completed courses, and ratings
"""

import os
from werkzeug.security import generate_password_hash
from database.db import get_connection, get_db_cursor, init_db

# 1. Standard Skills Catalog
SAMPLE_SKILLS = [
    ("Python", "Programming"),
    ("Java", "Programming"),
    ("SQL", "Database"),
    ("Excel", "Data Analysis"),
    ("Statistics", "Data Science"),
    ("Pandas", "Data Science"),
    ("NumPy", "Data Science"),
    ("Machine Learning", "Artificial Intelligence"),
    ("Deep Learning", "Artificial Intelligence"),
    ("HTML", "Web Development"),
    ("CSS", "Web Development"),
    ("JavaScript", "Web Development"),
    ("React", "Web Development"),
    ("Flask", "Backend Development"),
    ("Spring Boot", "Backend Development"),
    ("Data Visualization", "Data Analysis"),
    ("Data Analysis", "Data Analysis"),
    ("Power BI", "Business Intelligence"),
    ("Tableau", "Business Intelligence"),
    ("Data Engineering", "Data Engineering"),
    ("ETL Pipelines", "Data Engineering"),
    ("Apache Spark", "Big Data"),
    ("Git", "Tools"),
    ("Docker", "DevOps")
]

# 2. Career Roles and required skills
SAMPLE_ROLES = [
    {
        "name": "Data Analyst",
        "description": "Analyzes complex datasets, builds dashboards, and delivers actionable business insights using SQL, Excel, and BI tools.",
        "skills": [
            ("SQL", "Required"),
            ("Excel", "Required"),
            ("Python", "Required"),
            ("Statistics", "Required"),
            ("Data Visualization", "Required"),
            ("Pandas", "Required"),
            ("Power BI", "Recommended"),
            ("Tableau", "Recommended")
        ]
    },
    {
        "name": "Data Engineer",
        "description": "Designs, builds, and maintains data pipelines, data warehouses, and distributed computing architectures.",
        "skills": [
            ("SQL", "Required"),
            ("Python", "Required"),
            ("Data Engineering", "Required"),
            ("ETL Pipelines", "Required"),
            ("Apache Spark", "Required"),
            ("Docker", "Recommended"),
            ("Git", "Recommended")
        ]
    },
    {
        "name": "Python Developer",
        "description": "Develops backend applications, APIs, automation scripts, and database-integrated services with Python.",
        "skills": [
            ("Python", "Required"),
            ("Flask", "Required"),
            ("SQL", "Required"),
            ("Git", "Required"),
            ("Docker", "Recommended"),
            ("Data Analysis", "Recommended")
        ]
    },
    {
        "name": "Java Developer",
        "description": "Constructs robust, scalable enterprise applications and microservices using Java and Spring Boot.",
        "skills": [
            ("Java", "Required"),
            ("Spring Boot", "Required"),
            ("SQL", "Required"),
            ("Git", "Required"),
            ("Docker", "Recommended")
        ]
    },
    {
        "name": "Web Developer",
        "description": "Builds interactive, modern web frontends and responsive user interfaces with HTML, CSS, JavaScript, and React.",
        "skills": [
            ("HTML", "Required"),
            ("CSS", "Required"),
            ("JavaScript", "Required"),
            ("React", "Required"),
            ("Git", "Required")
        ]
    },
    {
        "name": "Machine Learning Engineer",
        "description": "Designs, trains, and evaluates predictive machine learning models and deep neural networks on structured and unstructured data.",
        "skills": [
            ("Python", "Required"),
            ("Machine Learning", "Required"),
            ("Deep Learning", "Required"),
            ("Statistics", "Required"),
            ("Pandas", "Required"),
            ("NumPy", "Required"),
            ("Data Visualization", "Recommended")
        ]
    },
    {
        "name": "Software Engineer",
        "description": "Versatile full-stack engineer developing multi-tier software applications, system utilities, and database services.",
        "skills": [
            ("Python", "Required"),
            ("Java", "Required"),
            ("SQL", "Required"),
            ("Git", "Required"),
            ("HTML", "Recommended"),
            ("CSS", "Recommended"),
            ("JavaScript", "Recommended")
        ]
    }
]

# 3. Comprehensive Sample Courses
SAMPLE_COURSES = [
    {
        "course_code": "PY101",
        "title": "Python Programming Fundamentals",
        "description": "Learn syntax, data structures, control flow, functions, object-oriented concepts, and basic scripting in Python from scratch.",
        "category": "Programming",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 20,
        "skills": ["Python"],
        "target_roles": ["Python Developer", "Data Analyst", "Machine Learning Engineer", "Software Engineer"],
        "prereq_codes": []
    },
    {
        "course_code": "SQL101",
        "title": "SQL Fundamentals for Relational Databases",
        "description": "Master relational database concepts, SELECT statements, WHERE filters, aggregate functions, GROUP BY, and basic multi-table JOINs.",
        "category": "Database",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 15,
        "skills": ["SQL"],
        "target_roles": ["Data Analyst", "Data Engineer", "Python Developer", "Software Engineer"],
        "prereq_codes": []
    },
    {
        "course_code": "SQL201",
        "title": "Advanced SQL & Query Optimization",
        "description": "Deep dive into window functions, common table expressions (CTEs), subqueries, index strategies, execution plans, and performance tuning.",
        "category": "Database",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 18,
        "skills": ["SQL"],
        "target_roles": ["Data Analyst", "Data Engineer"],
        "prereq_codes": ["SQL101"]
    },
    {
        "course_code": "EXCEL101",
        "title": "Excel for Data Analysis & Reporting",
        "description": "Hands-on data cleaning, formulas (XLOOKUP, INDEX/MATCH), pivot tables, conditional formatting, and executive summary dashboards.",
        "category": "Data Analysis",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 12,
        "skills": ["Excel", "Data Analysis"],
        "target_roles": ["Data Analyst"],
        "prereq_codes": []
    },
    {
        "course_code": "STAT101",
        "title": "Statistics for Data Analysis & Machine Learning",
        "description": "Descriptive statistics, probability distributions, hypothesis testing, p-values, confidence intervals, regression analysis, and variance.",
        "category": "Data Science",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 18,
        "skills": ["Statistics", "Data Analysis"],
        "target_roles": ["Data Analyst", "Machine Learning Engineer"],
        "prereq_codes": []
    },
    {
        "course_code": "PY201",
        "title": "Data Wrangling with Pandas and NumPy",
        "description": "Perform high-performance data manipulation, filtering, merging, time-series operations, handling missing values, and NumPy vectorized calculations.",
        "category": "Data Science",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 22,
        "skills": ["Pandas", "NumPy", "Python", "Data Analysis"],
        "target_roles": ["Data Analyst", "Machine Learning Engineer", "Python Developer"],
        "prereq_codes": ["PY101"]
    },
    {
        "course_code": "VIZ101",
        "title": "Data Visualization with Matplotlib & Seaborn",
        "description": "Create publication-quality statistical charts, heatmaps, distribution plots, subplots, and visual data storytelling with Python.",
        "category": "Data Visualization",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 14,
        "skills": ["Data Visualization", "Python"],
        "target_roles": ["Data Analyst", "Machine Learning Engineer"],
        "prereq_codes": ["PY101"]
    },
    {
        "course_code": "BI101",
        "title": "Business Intelligence with Power BI",
        "description": "Connect diverse data sources, design star schema data models, author DAX calculated measures, and publish interactive corporate dashboards.",
        "category": "Business Intelligence",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 16,
        "skills": ["Power BI", "Data Visualization", "Data Analysis"],
        "target_roles": ["Data Analyst"],
        "prereq_codes": ["EXCEL101"]
    },
    {
        "course_code": "TAB101",
        "title": "Visual Analytics with Tableau",
        "description": "Build interactive worksheets, calculated fields, parameters, geographic mapping, and executive storyboards in Tableau Desktop.",
        "category": "Business Intelligence",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 15,
        "skills": ["Tableau", "Data Visualization", "Data Analysis"],
        "target_roles": ["Data Analyst"],
        "prereq_codes": []
    },
    {
        "course_code": "DE101",
        "title": "Data Engineering Fundamentals",
        "description": "Understand modern data architecture, OLAP vs OLTP, data lake vs warehouse, batch vs stream data, and dimensional modeling.",
        "category": "Data Engineering",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 25,
        "skills": ["Data Engineering", "SQL"],
        "target_roles": ["Data Engineer"],
        "prereq_codes": ["SQL101"]
    },
    {
        "course_code": "ETL201",
        "title": "Building Scalable ETL Pipelines",
        "description": "Design resilient Extract, Transform, Load workflows using Python, workflow orchestration, database connectors, and automated validation.",
        "category": "Data Engineering",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 24,
        "skills": ["ETL Pipelines", "Python", "SQL", "Data Engineering"],
        "target_roles": ["Data Engineer"],
        "prereq_codes": ["DE101", "PY101"]
    },
    {
        "course_code": "SPARK301",
        "title": "Apache Spark & Big Data Processing",
        "description": "Harness distributed PySpark DataFrames, Spark SQL, partitioned computations, memory management, and big data clustering on large datasets.",
        "category": "Big Data",
        "difficulty_level": "Advanced",
        "estimated_duration_hours": 30,
        "skills": ["Apache Spark", "Python", "Data Engineering"],
        "target_roles": ["Data Engineer"],
        "prereq_codes": ["ETL201"]
    },
    {
        "course_code": "ML201",
        "title": "Machine Learning from Scratch with Scikit-learn",
        "description": "Master supervised and unsupervised learning algorithms: linear/logistic regression, decision trees, random forests, clustering, model evaluation, and hyperparameter tuning.",
        "category": "Machine Learning",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 28,
        "skills": ["Machine Learning", "Python", "Pandas", "NumPy", "Statistics"],
        "target_roles": ["Machine Learning Engineer"],
        "prereq_codes": ["PY201", "STAT101"]
    },
    {
        "course_code": "DL301",
        "title": "Deep Learning & Neural Networks",
        "description": "Construct multi-layer perceptrons, convolutional neural networks (CNNs), recurrent networks, backpropagation mechanics, and model regularization.",
        "category": "Machine Learning",
        "difficulty_level": "Advanced",
        "estimated_duration_hours": 35,
        "skills": ["Deep Learning", "Machine Learning", "Python"],
        "target_roles": ["Machine Learning Engineer"],
        "prereq_codes": ["ML201"]
    },
    {
        "course_code": "WEB101",
        "title": "HTML5 and Modern CSS3 Web Design",
        "description": "Semantic HTML markup, CSS Flexbox, CSS Grid layouts, media queries for responsive mobile design, web typography, and accessibility.",
        "category": "Web Development",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 16,
        "skills": ["HTML", "CSS"],
        "target_roles": ["Web Developer", "Software Engineer"],
        "prereq_codes": []
    },
    {
        "course_code": "JS101",
        "title": "Modern JavaScript (ES6+) for Web Developers",
        "description": "DOM manipulation, asynchronous JavaScript (Promises, async/await), arrow functions, closures, fetch API, and event-driven architectures.",
        "category": "Web Development",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 22,
        "skills": ["JavaScript"],
        "target_roles": ["Web Developer", "Software Engineer"],
        "prereq_codes": ["WEB101"]
    },
    {
        "course_code": "REACT201",
        "title": "React Fundamentals & Single Page Apps",
        "description": "Build modern component-driven user interfaces using functional components, JSX, hooks (useState, useEffect, useContext), and API integration.",
        "category": "Web Development",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 26,
        "skills": ["React", "JavaScript"],
        "target_roles": ["Web Developer", "Software Engineer"],
        "prereq_codes": ["JS101"]
    },
    {
        "course_code": "JAVA101",
        "title": "Java Programming Essentials",
        "description": "Core Java syntax, OOP inheritance, polymorphism, interfaces, exception handling, collections framework, and JVM execution principles.",
        "category": "Programming",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 24,
        "skills": ["Java"],
        "target_roles": ["Java Developer", "Software Engineer"],
        "prereq_codes": []
    },
    {
        "course_code": "BOOT201",
        "title": "Enterprise Microservices with Spring Boot",
        "description": "Develop production-ready REST services using Spring Boot, Spring Data JPA, dependency injection, Hibernate, security, and SQLite/Postgres integration.",
        "category": "Backend Development",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 30,
        "skills": ["Spring Boot", "Java", "SQL"],
        "target_roles": ["Java Developer", "Software Engineer"],
        "prereq_codes": ["JAVA101"]
    },
    {
        "course_code": "FLASK201",
        "title": "REST API Development with Flask & Python",
        "description": "Build lightweight, efficient web APIs, route handling, request serialization, JWT authentication, and database ORM integration using Flask.",
        "category": "Backend Development",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 20,
        "skills": ["Flask", "Python", "SQL"],
        "target_roles": ["Python Developer", "Software Engineer"],
        "prereq_codes": ["PY101"]
    },
    {
        "course_code": "GIT101",
        "title": "Version Control with Git & GitHub Collaboration",
        "description": "Branching strategies, pull requests, resolving merge conflicts, rebasing, commit discipline, and open-source project collaboration workflow.",
        "category": "Tools",
        "difficulty_level": "Beginner",
        "estimated_duration_hours": 10,
        "skills": ["Git"],
        "target_roles": ["Software Engineer", "Web Developer", "Python Developer", "Java Developer", "Data Engineer"],
        "prereq_codes": []
    },
    {
        "course_code": "DOCKER201",
        "title": "Containerization Fundamentals with Docker",
        "description": "Containerize full-stack applications, write Dockerfiles, manage multi-container systems using Docker Compose, volume mounts, and network bridges.",
        "category": "DevOps",
        "difficulty_level": "Intermediate",
        "estimated_duration_hours": 18,
        "skills": ["Docker"],
        "target_roles": ["Data Engineer", "Software Engineer", "Python Developer"],
        "prereq_codes": []
    }
]


def seed_database(db_path: str = None) -> None:
    """Populates the database with initial catalog, skills, roles, admin user, and sample ratings."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # 1. Seed Skills
        skill_id_map = {}
        for name, category in SAMPLE_SKILLS:
            cursor.execute(
                "INSERT INTO skills (name, category) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET category=excluded.category",
                (name, category)
            )
        cursor.execute("SELECT id, name FROM skills")
        for row in cursor.fetchall():
            skill_id_map[row["name"].lower()] = row["id"]

        # 2. Seed Career Roles & Role Skills
        role_id_map = {}
        for role in SAMPLE_ROLES:
            cursor.execute(
                "INSERT INTO career_roles (name, description) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET description=excluded.description",
                (role["name"], role["description"])
            )
        cursor.execute("SELECT id, name FROM career_roles")
        for row in cursor.fetchall():
            role_id_map[row["name"].lower()] = row["id"]

        for role in SAMPLE_ROLES:
            r_id = role_id_map[role["name"].lower()]
            for skill_name, importance in role["skills"]:
                s_id = skill_id_map.get(skill_name.lower())
                if s_id:
                    cursor.execute(
                        "INSERT OR IGNORE INTO role_skills (role_id, skill_id, importance) VALUES (?, ?, ?)",
                        (r_id, s_id, importance)
                    )

        # 3. Seed Sample Courses
        course_id_map = {}
        for course in SAMPLE_COURSES:
            cursor.execute(
                """
                INSERT INTO courses (course_code, title, description, category, difficulty_level, estimated_duration_hours)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(course_code) DO UPDATE SET
                    title=excluded.title,
                    description=excluded.description,
                    category=excluded.category,
                    difficulty_level=excluded.difficulty_level,
                    estimated_duration_hours=excluded.estimated_duration_hours
                """,
                (
                    course["course_code"],
                    course["title"],
                    course["description"],
                    course["category"],
                    course["difficulty_level"],
                    course["estimated_duration_hours"]
                )
            )
        cursor.execute("SELECT id, course_code FROM courses")
        for row in cursor.fetchall():
            course_id_map[row["course_code"].upper()] = row["id"]

        # 4. Map Course Skills & Target Roles
        for course in SAMPLE_COURSES:
            c_id = course_id_map[course["course_code"].upper()]
            # skills taught
            for s_name in course["skills"]:
                s_id = skill_id_map.get(s_name.lower())
                if s_id:
                    cursor.execute(
                        "INSERT OR IGNORE INTO course_skills (course_id, skill_id) VALUES (?, ?)",
                        (c_id, s_id)
                    )
            # target roles
            for r_name in course["target_roles"]:
                r_id = role_id_map.get(r_name.lower())
                if r_id:
                    cursor.execute(
                        "INSERT OR IGNORE INTO course_target_roles (course_id, role_id) VALUES (?, ?)",
                        (c_id, r_id)
                    )

        # 5. Map Course Prerequisites
        for course in SAMPLE_COURSES:
            c_id = course_id_map[course["course_code"].upper()]
            for prereq_code in course["prereq_codes"]:
                prereq_id = course_id_map.get(prereq_code.upper())
                if prereq_id:
                    cursor.execute(
                        "SELECT id FROM course_prerequisites WHERE course_id = ? AND prerequisite_course_id = ?",
                        (c_id, prereq_id)
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO course_prerequisites (course_id, prerequisite_course_id, note) VALUES (?, ?, ?)",
                            (c_id, prereq_id, f"Prerequisite: {prereq_code}")
                        )

        # 6. Seed Administrator Account if not present
        admin_email = os.getenv("ADMIN_EMAIL", "admin@codegnan.com").strip().lower()
        admin_name = os.getenv("ADMIN_NAME", "Codegnan Admin").strip()
        admin_pass = os.getenv("ADMIN_PASSWORD", "AdminSecurePass2026!")

        cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
        admin_row = cursor.fetchone()
        if not admin_row:
            hashed_admin_pass = generate_password_hash(admin_pass)
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                (admin_name, admin_email, hashed_admin_pass)
            )

        # 7. Seed Demo Student Accounts with real baseline interactions
        demo_student_email = "student@codegnan.com"
        cursor.execute("SELECT id FROM users WHERE email = ?", (demo_student_email,))
        demo_student = cursor.fetchone()
        if not demo_student:
            student_pass = generate_password_hash("StudentPass2026!")
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, 'student')",
                ("Priya Sharma", demo_student_email, student_pass)
            )
            student_id = cursor.lastrowid

            # Create Student Profile
            cursor.execute(
                """
                INSERT INTO student_profiles (user_id, target_role, preferred_difficulty, weekly_study_hours)
                VALUES (?, 'Data Analyst', 'Intermediate', 12)
                """,
                (student_id,)
            )

            # Assign initial skills: Excel, Python
            excel_id = skill_id_map.get("excel")
            python_id = skill_id_map.get("python")
            if excel_id:
                cursor.execute("INSERT OR IGNORE INTO student_skills (student_id, skill_id) VALUES (?, ?)", (student_id, excel_id))
            if python_id:
                cursor.execute("INSERT OR IGNORE INTO student_skills (student_id, skill_id) VALUES (?, ?)", (student_id, python_id))

            # Assign interests
            cursor.execute("INSERT OR IGNORE INTO student_interests (student_id, interest) VALUES (?, ?)", (student_id, "Data Analysis"))
            cursor.execute("INSERT OR IGNORE INTO student_interests (student_id, interest) VALUES (?, ?)", (student_id, "Machine Learning"))

            # Completed course: EXCEL101 with 5-star rating
            excel_course_id = course_id_map.get("EXCEL101")
            if excel_course_id:
                cursor.execute(
                    "INSERT OR IGNORE INTO enrollments (user_id, course_id, status, completed_at) VALUES (?, ?, 'Completed', CURRENT_TIMESTAMP)",
                    (student_id, excel_course_id)
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO ratings (user_id, course_id, rating, review) VALUES (?, ?, 5, 'Great practical guide to Excel and pivot tables!')",
                    (student_id, excel_course_id)
                )

            # Enrolled course: PY101 in progress
            py_course_id = course_id_map.get("PY101")
            if py_course_id:
                cursor.execute(
                    "INSERT OR IGNORE INTO enrollments (user_id, course_id, status) VALUES (?, ?, 'In Progress')",
                    (student_id, py_course_id)
                )

        # 8. Add a few more peer ratings for diverse feedback data
        peer_student_email = "rahul.demo@codegnan.com"
        cursor.execute("SELECT id FROM users WHERE email = ?", (peer_student_email,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, 'student')",
                ("Rahul Verma", peer_student_email, generate_password_hash("RahulPass2026!"))
            )
            rahul_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO student_profiles (user_id, target_role, preferred_difficulty, weekly_study_hours) VALUES (?, 'Machine Learning Engineer', 'Advanced', 15)",
                (rahul_id,)
            )
            # Rahul completed SQL101 and PY101
            for code, rating, rev in [
                ("SQL101", 5, "Very clear breakdown of SQL JOINs and grouping."),
                ("PY101", 4, "Strong introduction to Python OOP and functions."),
                ("ML201", 5, "Excellent hands-on machine learning projects!")
            ]:
                cid = course_id_map.get(code)
                if cid:
                    cursor.execute(
                        "INSERT OR IGNORE INTO enrollments (user_id, course_id, status, completed_at) VALUES (?, ?, 'Completed', CURRENT_TIMESTAMP)",
                        (rahul_id, cid)
                    )
                    cursor.execute(
                        "INSERT OR IGNORE INTO ratings (user_id, course_id, rating, review) VALUES (?, ?, ?, ?)",
                        (rahul_id, cid, rating, rev)
                    )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("Initializing database and seeding catalog...")
    seed_database()
    print("Database initialization and seed complete!")
