import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "lms.db"

def create_users_table():
    """Create users table for registration and login"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()
    print("✓ Users table created successfully or already exists...")


def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, email, password, full_name):
    """Register a new user"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        hashed_password = hash_password(password)
        
        cursor.execute("""
        INSERT INTO users (username, email, password, full_name)
        VALUES (?, ?, ?, ?)
        """, (username, email, hashed_password, full_name))
        
        conn.commit()
        conn.close()
        return True, "Registration successful! You can now login."
    
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            return False, "Username already exists. Please choose another."
        elif "email" in str(e):
            return False, "Email already registered. Please use another email."
        else:
            return False, "Registration failed. Please try again."
    except Exception as e:
        conn.close()
        return False, f"Error: {str(e)}"


def login_user(username, password):
    """Authenticate user and return user data"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        hashed_password = hash_password(password)
        
        cursor.execute("""
        SELECT id, username, email, full_name FROM users
        WHERE username = ? AND password = ?
        """, (username, hashed_password))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (user[0],))
            conn.commit()
            conn.close()
            return True, {"id": user[0], "username": user[1], "email": user[2], "full_name": user[3]}
        else:
            conn.close()
            return False, "Invalid username or password."
    
    except Exception as e:
        conn.close()
        return False, f"Login error: {str(e)}"


def user_exists(username):
    """Check if username exists"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None


def get_user_by_id(user_id):
    """Get user information by ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, username, email, full_name, created_at, last_login FROM users
    WHERE id = ?
    """, (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "full_name": user[3],
            "created_at": user[4],
            "last_login": user[5]
        }
    return None


def get_all_users():
    """Get all registered users (admin function)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, username, email, full_name, created_at, last_login FROM users
    """)
    
    users = cursor.fetchall()
    conn.close()
    
    return users


def delete_user(user_id):
    """Delete a user account"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True, "User deleted successfully."
    except Exception as e:
        conn.close()
        return False, f"Error: {str(e)}"


# Initialize the database when module is imported
if __name__ == "__main__":
    create_users_table()
