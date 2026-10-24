"""
Unit tests for course catalog search, filtering, and sorting.
"""

import tempfile
import os
import pytest
from database.seed_data import seed_database
from modules.course_catalog import get_courses, get_all_categories


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(db_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_course_search_and_filter(temp_db):
    """Verifies that search query and category filters operate properly."""
    # 1. Search for 'Python'
    py_courses = get_courses(search_query="Python", db_path=temp_db)
    assert len(py_courses) > 0
    for c in py_courses:
        assert "python" in c["title"].lower() or "python" in c["description"].lower() or "py" in c["course_code"].lower()

    # 2. Filter by Category 'Database'
    db_courses = get_courses(category="Database", db_path=temp_db)
    assert len(db_courses) >= 2
    for c in db_courses:
        assert c["category"] == "Database"

    # 3. Filter by Difficulty 'Beginner'
    beg_courses = get_courses(difficulty="Beginner", db_path=temp_db)
    assert len(beg_courses) > 0
    for c in beg_courses:
        assert c["difficulty_level"] == "Beginner"


def test_category_list_retrieval(temp_db):
    """Verifies that all seeded categories are retrieved."""
    categories = get_all_categories()
    assert len(categories) >= 5
    assert "Programming" in categories
    assert "Database" in categories
    assert "Machine Learning" in categories
