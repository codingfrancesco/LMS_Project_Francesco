import sqlite3

def create_users_table(db_name="user_data.db"):
    conn = None  # Initialize conn to None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create the users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                chapter TEXT NOT NULL,
                mcqs_content TEXT,
                option1 text,
                option2 text,
                option3 text,
                option4 text
                      
            )
        """)
        conn.commit()
        print("Table 'users' created successfully or already exists.")

    except sqlite3.Error as e:
        print(f"Error creating table: {e}")
    finally:
        if conn:
            conn.close()

# Example usage:
create_users_table("my_database.db")



