import sqlite3 

def create_assignments_table(db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title unique,
        description TEXT,
        deadline TEXT,
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );""")
    conn.commit()
    conn.close()
    print("Table 'assignments' created successfully or already exists...")

def insert_assignments(course_id, title, description, deadline, db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO assignments (course_id, title, description, deadline)
        VALUES (?, ?, ?, ? )                
 """, (course_id, title, description, deadline))
    
    conn.commit()
    conn.close()
    print("assignments inserted successfully.")


