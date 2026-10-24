-- Database Schema for Personalized Course Recommendation System
-- Codegnan AI Avengers Hackathon

PRAGMA foreign_keys = ON;

-- 1. Users Table (Students & Admins)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Skills Catalog
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
    category TEXT DEFAULT 'General'
);

-- 3. Career Roles Catalog
CREATE TABLE IF NOT EXISTS career_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
    description TEXT
);

-- 4. Role - Skill Requirements Mapping
CREATE TABLE IF NOT EXISTS role_skills (
    role_id INTEGER NOT NULL REFERENCES career_roles(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    importance TEXT DEFAULT 'Required' CHECK(importance IN ('Required', 'Recommended')),
    PRIMARY KEY (role_id, skill_id)
);

-- 5. Student Profiles
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role TEXT DEFAULT 'Data Analyst',
    preferred_difficulty TEXT DEFAULT 'All' CHECK(preferred_difficulty IN ('All', 'Beginner', 'Intermediate', 'Advanced')),
    weekly_study_hours INTEGER DEFAULT 10,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Student Skills (Current Skills Possessed)
CREATE TABLE IF NOT EXISTS student_skills (
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, skill_id)
);

-- 7. Student Interests
CREATE TABLE IF NOT EXISTS student_interests (
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interest TEXT NOT NULL,
    PRIMARY KEY (student_id, interest)
);

-- 8. Course Catalog
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL COLLATE NOCASE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty_level TEXT NOT NULL CHECK(difficulty_level IN ('Beginner', 'Intermediate', 'Advanced')),
    estimated_duration_hours INTEGER NOT NULL CHECK(estimated_duration_hours > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Course - Skills Taught Mapping
CREATE TABLE IF NOT EXISTS course_skills (
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, skill_id)
);

-- 10. Course Prerequisites (Skill or Prior Course)
CREATE TABLE IF NOT EXISTS course_prerequisites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    prerequisite_course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    prerequisite_skill_id INTEGER REFERENCES skills(id) ON DELETE SET NULL,
    note TEXT
);

-- 11. Course - Target Job Roles Mapping
CREATE TABLE IF NOT EXISTS course_target_roles (
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES career_roles(id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, role_id)
);

-- 12. Enrollments Table
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'Enrolled' CHECK(status IN ('Enrolled', 'In Progress', 'Completed')),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(user_id, course_id)
);

-- 13. Course Ratings and Feedback
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, course_id)
);

-- Indexes for optimal lookup performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_ratings_course ON ratings(course_id);
CREATE INDEX IF NOT EXISTS idx_course_skills_course ON course_skills(course_id);
CREATE INDEX IF NOT EXISTS idx_role_skills_role ON role_skills(role_id);
