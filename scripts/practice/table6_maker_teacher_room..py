# Teaplcease make a database table in which we have teacher name, time he came and time he left 

import sqlite3 

def create_users_table(db_name="user_data.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        time_he_left TEXT NOT NULL,
        time_he_came TEXT
    ) 
    """)
    conn.commit()
    print("Table 'teacher' created succesfully or already exists")

create_users_table()

### DONE!!!!