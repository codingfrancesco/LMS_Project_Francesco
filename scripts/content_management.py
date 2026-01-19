import sqlite3
from datetime import datetime

DB_NAME = "lms.db"

def create_content_tables():
    """Create tables for courses, lessons, and assignments"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Lessons table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        order_num INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );
    """)

    # Assignments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );
    """)

    conn.commit()
    conn.close()
    print("✓ Content tables created successfully...")


# ===== COURSE FUNCTIONS =====
def add_course(title, description, instructor_id):
    """Add a new course"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO courses (title, description)
        VALUES (?, ?)
        """, (title, description))
        
        conn.commit()
        course_id = cursor.lastrowid
        conn.close()
        return True, course_id, f"✓ Course '{title}' created successfully!"
    
    except sqlite3.IntegrityError:
        conn.close()
        return False, None, "✗ Course title already exists."
    except Exception as e:
        conn.close()
        return False, None, f"✗ Error: {str(e)}"


def get_all_courses():
    """Get all courses"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, title, description FROM courses
    """)
    
    courses = cursor.fetchall()
    conn.close()
    return courses


def get_course_by_id(course_id):
    """Get course details by ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, title, description FROM courses
    WHERE id = ?
    """, (course_id,))
    
    course = cursor.fetchone()
    conn.close()
    return course


def delete_course(course_id):
    """Delete a course"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
        conn.close()
        return True, "✓ Course deleted successfully."
    except Exception as e:
        conn.close()
        return False, f"✗ Error: {str(e)}"


# ===== LESSON FUNCTIONS =====
def add_lesson(course_id, title, content):
    """Add a new lesson to a course"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Get next order number
        cursor.execute("""
        SELECT MAX(order_num) FROM lessons WHERE course_id = ?
        """, (course_id,))
        
        result = cursor.fetchone()
        next_order = (result[0] or 0) + 1
        
        cursor.execute("""
        INSERT INTO lessons (course_id, title, content, order_num)
        VALUES (?, ?, ?, ?)
        """, (course_id, title, content, next_order))
        
        conn.commit()
        lesson_id = cursor.lastrowid
        conn.close()
        return True, lesson_id, f"✓ Lesson '{title}' added successfully!"
    
    except Exception as e:
        conn.close()
        return False, None, f"✗ Error: {str(e)}"


def get_lessons_by_course(course_id):
    """Get all lessons for a course"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, course_id, title, content, order_num FROM lessons
    WHERE course_id = ?
    ORDER BY order_num
    """, (course_id,))
    
    lessons = cursor.fetchall()
    conn.close()
    return lessons


def get_lesson_by_id(lesson_id):
    """Get lesson details"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, course_id, title, content, order_num FROM lessons
    WHERE id = ?
    """, (lesson_id,))
    
    lesson = cursor.fetchone()
    conn.close()
    return lesson


def delete_lesson(lesson_id):
    """Delete a lesson"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
        conn.commit()
        conn.close()
        return True, "✓ Lesson deleted successfully."
    except Exception as e:
        conn.close()
        return False, f"✗ Error: {str(e)}"


# ===== ASSIGNMENT FUNCTIONS =====
def add_assignment(course_id, title, description, due_date):
    """Add a new assignment to a course"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO assignments (course_id, title, description, due_date)
        VALUES (?, ?, ?, ?)
        """, (course_id, title, description, due_date))
        
        conn.commit()
        assignment_id = cursor.lastrowid
        conn.close()
        return True, assignment_id, f"✓ Assignment '{title}' created successfully!"
    
    except Exception as e:
        conn.close()
        return False, None, f"✗ Error: {str(e)}"


def get_assignments_by_course(course_id):
    """Get all assignments for a course"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, course_id, title, description, due_date FROM assignments
    WHERE course_id = ?
    ORDER BY due_date
    """, (course_id,))
    
    assignments = cursor.fetchall()
    conn.close()
    return assignments


def get_assignment_by_id(assignment_id):
    """Get assignment details"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, course_id, title, description, due_date FROM assignments
    WHERE id = ?
    """, (assignment_id,))
    
    assignment = cursor.fetchone()
    conn.close()
    return assignment


def delete_assignment(assignment_id):
    """Delete an assignment"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        conn.commit()
        conn.close()
        return True, "✓ Assignment deleted successfully."
    except Exception as e:
        conn.close()
        return False, f"✗ Error: {str(e)}"


if __name__ == "__main__":
    create_content_tables()
