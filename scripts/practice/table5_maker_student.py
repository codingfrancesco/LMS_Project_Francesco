# make a code to create table named student
# column 1 name
# column 2 is age
# column 3 is project name



import sqlite3

def create_users_table(db_name="user_data.db"):
    conn =  sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS  student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        age TEXT NOT NULL,
        projectname TEXT
    )
    """)
    conn.commit()
    print("Table 'student' created succesfully or already exists")
        
create_users_table()
