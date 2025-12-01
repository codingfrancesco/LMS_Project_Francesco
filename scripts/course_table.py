import sqlite3
def create_courses_table(db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT NOT NULL UNIQUE,
        description TEXT );
""")
    conn.commit()
    conn.close()
    print("Table 'courses' created successfully or already exists..." )



def insert_course(title, description, course_id, db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT or ignore INTO courses (title, description, course_id)
        VALUES (?,?,?)
    """, (title, description, course_id))

    conn.commit()
    conn.close()
    print("Course inserted successfully.")
