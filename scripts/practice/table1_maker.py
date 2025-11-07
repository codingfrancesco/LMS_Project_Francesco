import sqlite3

def create_users_table(db_name="user_data.db"):
    conn = None  # Initialize conn to None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create the users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT
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
create_users_table()



