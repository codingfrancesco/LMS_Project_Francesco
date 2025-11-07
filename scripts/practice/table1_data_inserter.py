
import sqlite3

def data_inserter(user,role,passw,db_name="user_data.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, (user, passw, role))

    conn.commit()
    conn.close()
    print("User data inserted successfully.")

    

data_inserter("fran","123","student")

## make insert table for table 2 and table 3