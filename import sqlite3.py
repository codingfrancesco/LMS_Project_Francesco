import sqlite3
import os

db_path = "lms.db"

# Check if database exists
if os.path.exists(db_path):
    print(f"✅ Database file exists: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("=" * 60)
    print("DATABASE TABLES:")
    print("=" * 60)
    
    for table in tables:
        table_name = table[0]
        print(f"\n📋 Table: {table_name}")
        print("-" * 60)
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            null_str = "NOT NULL" if not_null else "NULL"
            pk_str = "PRIMARY KEY" if pk else ""
            print(f"  • {col_name} ({col_type}) {null_str} {pk_str}".strip())
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"\nRows: {count}")
        
        # Show sample data if table has rows
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            print("\nSample data (first 3 rows):")
            for row in rows:
                print(f"  {row}")
    
    conn.close()
    
else:
    print(f"❌ Database file not found: {db_path}")