# table anme will be store
# column 1 will be fruit
# column 2 will be price


import sqlite3

def create_users_table(db_name="user_data.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fruit TEXT NOT NULL UNIQUE,
        price INTEGER NOT NULL)
    """)
    conn.commit()
    print("Table 'store' created succesfully or already exists.")

create_users_table("my_database.db")
