import sqlite3
def create_lessons_table(db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT NOT NULL UNIQUE,
        description TEXT );
""")
    conn.commit()
    conn.close()
    print("Table 'lessons' created successfully or already exists..." )



def insert_lessons(title, description, course_id, db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT or ignore INTO courses (title, description, course_id)
        VALUES (?,?,?)
    """, (title, description, course_id))

    conn.commit()
    conn.close()
    print("lesson inserted successfully.")

def make_list_lesson():
    conn = sqlite3.connect("lms.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lessons")
    lessons = cursor.fetchall()

    conn.close()
    return lessons
