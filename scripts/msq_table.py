import sqlite3


def create_msqs_table(db_name="lms.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS msqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER,
        question TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_answer TEXT,
        wrong_answer TEXT,
        FOREIGN KEY (topic_id) REFERENCES topics(id)
);""")
    conn.commit()
    conn.close()
    print("Table 'msqs' created successfully or already exists...")




def insert_msq(topic_id, question, option_a, option_b, option_c, option_d, correct_answer, db_name="lms.db"):   
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO msqs (topic_id, question, option_a, option_b, option_c, option_d, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (topic_id, question, option_a, option_b, option_c, option_d, correct_answer))

    conn.commit()
    conn.close()
    print("MSQ inserted successfully.")