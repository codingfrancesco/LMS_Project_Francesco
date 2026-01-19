import sqlite3
import hashlib
from scripts.users_database import hash_password, DB_NAME

def add_admin_user(username, email, password, full_name):
    """Add an admin user to the database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # First, check if users table has is_admin column
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_admin' not in columns:
            # Add is_admin column if it doesn't exist
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("✓ Added 'is_admin' column to users table")
        
        # Insert admin user
        hashed_password = hash_password(password)
        cursor.execute("""
        INSERT INTO users (username, email, password, full_name, is_admin)
        VALUES (?, ?, ?, ?, 1)
        """, (username, email, hashed_password, full_name))
        
        conn.commit()
        conn.close()
        return True, f"✓ Admin user '{username}' created successfully!"
    
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            return False, "✗ Username already exists."
        elif "email" in str(e):
            return False, "✗ Email already registered."
        else:
            return False, f"✗ Error: {str(e)}"
    except Exception as e:
        conn.close()
        return False, f"✗ Error: {str(e)}"


def make_user_admin(username):
    """Convert an existing user to admin"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
        
        if cursor.rowcount == 0:
            conn.close()
            return False, f"✗ User '{username}' not found."
        
        conn.commit()
        conn.close()
        return True, f"✓ User '{username}' is now an admin!"
    
    except Exception as e:
        conn.close()
        return False, f"✗ Error: {str(e)}"


def is_admin(user_id):
    """Check if user is admin"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] == 1 if result else False


def get_all_admins():
    """Get all admin users"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, username, email, full_name FROM users WHERE is_admin = 1
    """)
    
    admins = cursor.fetchall()
    conn.close()
    
    return admins


if __name__ == "__main__":
    # Create a default admin account
    success, message = add_admin_user(
        username="admin",
        email="admin@lms.edu",
        password="admin123",
        full_name="Administrator"
    )
    print(message)
    
    if success:
        print("\n📝 Admin Account Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@lms.edu")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
