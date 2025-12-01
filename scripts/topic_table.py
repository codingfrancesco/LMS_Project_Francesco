import sqlite3

def create_topics_table(db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT unique,
        subtitle TEXT,
        FOREIGN KEY (course_id) REFERENCES courses(id)
 );""")
    conn.commit()
    conn.close()
    print("Table 'topics' created successfully or already exists...")

    
def insert_topic(course_id, title, db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT or ignore INTO topics (course_id, title)
        VALUES (?, ?)
    """, (course_id, title))

    conn.commit()
    conn.close()
    print("Topic inserted successfully.")

