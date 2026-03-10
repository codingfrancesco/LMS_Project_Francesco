# Import Flask framework for creating web application
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
# Import sqlite3 for database operations
import sqlite3
# Import hashlib for password hashing (security)
import hashlib
# Import os for secret key generation
import os

# Initialize Flask application
app = Flask(__name__)
# Set secret key for session management (used for encrypting session data)
# This ensures user sessions are secure and cannot be tampered with
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Function to establish database connection
def get_db_connection(db_name="lms.db"):
    """
    Connect to the SQLite database and return connection object.
    
    Args:
        db_name (str): Name of the database file, defaults to "lms.db"
    
    Returns:
        sqlite3.Connection: Database connection object with Row factory
    """
    # Connect to the specified SQLite database file
    conn = sqlite3.connect(db_name)
    # Set row_factory to sqlite3.Row to access columns by name (dict-like)
    # This allows us to use column names instead of column indices
    conn.row_factory = sqlite3.Row
    return conn


# Function to hash passwords for secure storage
def hash_password(password):
    """
    Hash a password using SHA256 algorithm.
    
    Args:
        password (str): Plain text password to hash
    
    Returns:
        str: Hashed password (hexadecimal string)
    """
    # Use SHA256 to hash the password for security
    # This ensures passwords are not stored in plain text
    return hashlib.sha256(password.encode()).hexdigest()


# Function to initialize database tables on first run
def init_db():
    """
    Create necessary database tables if they don't exist.
    
    Creates tables for:
    - users: Store user account information
    - courses: Store course information
    - topics: Store lesson topics within courses
    - msqs: Store multiple choice questions for assignments
    """
    # Establish connection to the database
    conn = get_db_connection()
    # Create cursor object to execute SQL commands
    cursor = conn.cursor()
    
    # Create users table for storing user account information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            -- Unique identifier for each user (auto-incrementing primary key)
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Username must be unique (no two users can have same username)
            username TEXT NOT NULL UNIQUE,
            -- Email must be unique (no two users can have same email)
            email TEXT NOT NULL UNIQUE,
            -- Password stored as hashed string (never plain text)
            password TEXT NOT NULL,
            -- Full name of the user
            full_name TEXT NOT NULL,
            -- User role: either 'student' or 'teacher'
            role TEXT NOT NULL DEFAULT 'student',
            -- Timestamp when account was created (automatic)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Timestamp of last login
            last_login TIMESTAMP
        )
    """)
    
    # Create courses table for storing course information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            -- Unique identifier for each course
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Unique course ID number
            course_id INTEGER,
            -- Course title (must be unique)
            title TEXT NOT NULL UNIQUE,
            -- Description of what the course covers
            description TEXT,
            -- Type of course (Self-Paced, Instructor-Led, Hybrid, Workshop)
            course_type TEXT DEFAULT 'Self-Paced',
            -- Duration of the course (e.g., "4 weeks", "20 hours")
            duration TEXT DEFAULT 'Flexible',
            -- Difficulty level (Beginner, Intermediate, Advanced, Expert)
            level TEXT DEFAULT 'Beginner',
            -- ID of the teacher who created this course
            teacher_id INTEGER,
            -- Timestamp when course was created
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign key linking to the teacher user
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        )
    """)

    # Migration: ensure `courses` table has expected columns when upgrading from older schema
    try:
        cursor.execute("PRAGMA table_info(courses)")
        existing_cols = [row['name'] for row in cursor.fetchall()]

        columns_to_add = {
            'course_id': "INTEGER",
            'course_type': "TEXT DEFAULT 'Self-Paced'",
            'duration': "TEXT DEFAULT 'Flexible'",
            'level': "TEXT DEFAULT 'Beginner'",
            'teacher_id': "INTEGER",
            'created_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        for col, definition in columns_to_add.items():
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE courses ADD COLUMN {col} {definition}")
                except sqlite3.OperationalError:
                    # If ALTER TABLE fails for any reason, ignore and continue - table will still be usable
                    pass
    except Exception:
        # If PRAGMA or inspection fails, continue without raising to avoid breaking init on older DBs
        pass
    
    # Create topics table for storing lesson topics within courses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            -- Unique identifier for each topic
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the course this topic belongs to
            course_id INTEGER NOT NULL,
            -- Topic title (must be unique)
            title TEXT UNIQUE,
            -- Optional subtitle or description
            subtitle TEXT,
            -- Lesson content (body text for the lesson)
            content TEXT,
            -- Timestamp when topic was created
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign key linking to courses table
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
    # Migration: ensure `topics` table has content column
    try:
        cursor.execute("PRAGMA table_info(topics)")
        existing_cols = [row['name'] for row in cursor.fetchall()]
        if 'content' not in existing_cols:
            try:
                cursor.execute("ALTER TABLE topics ADD COLUMN content TEXT")
            except sqlite3.OperationalError:
                pass
    except Exception:
        pass
    
    # Create msqs table for storing multiple choice questions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS msqs (
            -- Unique identifier for each question
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the topic this question belongs to
            topic_id INTEGER NOT NULL,
            -- The question text
            question TEXT NOT NULL,
            -- Option A text
            option_a TEXT NOT NULL,
            -- Option B text
            option_b TEXT NOT NULL,
            -- Option C text
            option_c TEXT NOT NULL,
            -- Option D text
            option_d TEXT NOT NULL,
            -- Correct answer: 'a', 'b', 'c', or 'd'
            correct_answer TEXT NOT NULL,
            -- Timestamp when question was created
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign key linking to topics table
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    
    # Create enrollments table to track which students are enrolled in which courses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            -- Unique identifier for each enrollment
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the student
            student_id INTEGER NOT NULL,
            -- ID of the course
            course_id INTEGER NOT NULL,
            -- Timestamp when student enrolled
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Student's progress percentage (0-100)
            progress INTEGER DEFAULT 0,
            -- Foreign keys
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            -- Unique constraint: each student can only enroll once per course
            UNIQUE(student_id, course_id)
        )
    """)
    
    # Create submissions table to track student assignment submissions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            -- Unique identifier for each submission
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the student submitting
            student_id INTEGER NOT NULL,
            -- ID of the question being answered
            question_id INTEGER NOT NULL,
            -- Student's selected answer: 'a', 'b', 'c', or 'd'
            selected_answer TEXT NOT NULL,
            -- Whether the answer is correct (1 for correct, 0 for incorrect)
            is_correct INTEGER DEFAULT 0,
            -- Timestamp when answer was submitted
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign keys
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES msqs(id)
        )
    """)
    
    # Create attendance table to track student attendance in lessons
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            -- Unique identifier for each attendance record
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the student
            student_id INTEGER NOT NULL,
            -- ID of the lesson/topic
            lesson_id INTEGER NOT NULL,
            -- ID of the course
            course_id INTEGER NOT NULL,
            -- Attendance status: 'present', 'absent', 'late'
            status TEXT DEFAULT 'absent',
            -- Date of the lesson
            lesson_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Timestamp when attendance was recorded
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign keys
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (lesson_id) REFERENCES topics(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
    # Create notifications table to notify students of new lessons and assignments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            -- Unique identifier for each notification
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the student receiving the notification
            student_id INTEGER NOT NULL,
            -- ID of the course
            course_id INTEGER NOT NULL,
            -- Type of notification: 'lesson', 'assignment'
            notification_type TEXT NOT NULL,
            -- Title of the notification
            title TEXT NOT NULL,
            -- Message content
            message TEXT,
            -- Link to the resource (lesson_id or assignment_id)
            resource_id INTEGER,
            -- Whether the notification has been read
            is_read INTEGER DEFAULT 0,
            -- Timestamp when notification was created
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign keys
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
    # Create grades table to store assignment grades and teacher feedback
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            -- Unique identifier for each grade record
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the student being graded
            student_id INTEGER NOT NULL,
            -- ID of the assignment being graded
            assignment_id INTEGER NOT NULL,
            -- ID of the teacher giving the grade
            teacher_id INTEGER NOT NULL,
            -- Numeric grade (0-100)
            grade REAL,
            -- Feedback comments from the teacher
            feedback TEXT,
            -- Timestamp when grade was given
            graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Timestamp when last updated
            updated_at TIMESTAMP,
            -- Foreign keys
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (assignment_id) REFERENCES assignments(id),
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        )
    """)
    
    # Create comments table for course discussions and student interactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            -- Unique identifier for each comment
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- ID of the user posting the comment
            user_id INTEGER NOT NULL,
            -- ID of the course the comment is about
            course_id INTEGER NOT NULL,
            -- Content of the comment/message
            message TEXT NOT NULL,
            -- Timestamp when comment was created
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign keys
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
    # Commit all changes to the database
    conn.commit()
    # Close the database connection
    conn.close()


# Function to safely execute SELECT query with error handling
def safe_count_query(query, db_name="lms.db"):
    """
    Safely execute a COUNT query and return the count.
    Returns 0 if table doesn't exist.
    
    Args:
        query (str): SQL query to execute
        db_name (str): Name of the database file
    
    Returns:
        int: Count result or 0 if table doesn't exist
    """
    try:
        # Try to execute the query
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        # Execute the SQL query
        cursor.execute(query)
        # Fetch the result and get the count value
        result = cursor.fetchone()['count']
        # Close the connection
        conn.close()
        # Return the count
        return result
    except sqlite3.OperationalError:
        # If table doesn't exist, return 0 instead of crashing
        return 0


# Define route for homepage
@app.route("/")
def home():
    """
    Render the home page with statistics from the database.
    
    Fetches:
    - Total count of courses
    - Total count of topics
    - Total count of registered users
    
    Returns:
        Rendered HTML template with statistics
    """
    # Safely count courses - returns 0 if courses table doesn't exist
    courses_count = safe_count_query("SELECT COUNT(*) as count FROM courses")
    
    # Safely count topics - returns 0 if topics table doesn't exist
    topics_count = safe_count_query("SELECT COUNT(*) as count FROM topics")
    
    # Safely count users - returns 0 if users table doesn't exist
    users_count = safe_count_query("SELECT COUNT(*) as count FROM users")
    
    # Check if user is logged in
    is_logged_in = 'user_id' in session
    
    # Render home.html template and pass the statistics as variables
    # These variables can be used in the HTML template with {{ variable_name }}
    return render_template('home.html', 
                         courses_count=courses_count,
                         topics_count=topics_count,
                         users_count=users_count,
                         is_logged_in=is_logged_in)


# Define route for registration page (GET and POST)
@app.route("/register", methods=['GET', 'POST'])
def register():
    """
    Handle user registration for both GET (display form) and POST (process form).
    
    GET: Display registration form
    POST: Process registration form submission
    
    Returns:
        GET: Rendered registration form template
        POST: Redirect to login page on success or back to register on error
    """
    # If request is POST (form submission)
    if request.method == 'POST':
        # Extract form data from the registration form
        # request.form.get() safely gets form values or None if not present
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        role = request.form.get('role', 'student')  # Default to student if not specified
        
        # Validation: Check if all required fields are filled
        if not username or not email or not password or not full_name:
            # Return error message if any field is empty
            return render_template('register.html', error='All fields are required!')
        
        # Validation: Check if passwords match
        if password != confirm_password:
            # Return error message if passwords don't match
            return render_template('register.html', error='Passwords do not match!')
        
        # Validation: Check password length (security requirement)
        if len(password) < 6:
            # Return error message if password is too short
            return render_template('register.html', error='Password must be at least 6 characters!')
        
        try:
            # Establish connection to the database
            conn = get_db_connection()
            # Create cursor object to execute SQL commands
            cursor = conn.cursor()
            
            # Hash the password for secure storage
            hashed_password = hash_password(password)
            
            # Execute SQL INSERT to add new user to database
            cursor.execute("""
                INSERT INTO users (username, email, password, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, hashed_password, full_name, role))
            
            # Commit the changes to the database
            conn.commit()
            # Close the connection
            conn.close()
            
            # Redirect to login page after successful registration
            return redirect(url_for('login'))
        
        except sqlite3.IntegrityError:
            # Handle duplicate username or email
            return render_template('register.html', error='Username or email already exists!')
    
    # If request is GET (display form)
    # Render the registration form template
    return render_template('register.html')


# Define route for login page (GET and POST)
@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    Handle user login for both GET (display form) and POST (process form).
    
    GET: Display login form
    POST: Process login credentials and create session
    
    Returns:
        GET: Rendered login form template
        POST: Redirect to dashboard on success or back to login on error
    """
    # If request is POST (form submission)
    if request.method == 'POST':
        # Extract form data from the login form
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validation: Check if both username and password are provided
        if not username or not password:
            # Return error message if any field is empty
            return render_template('login.html', error='Username and password are required!')
        
        try:
            # Establish connection to the database
            conn = get_db_connection()
            # Create cursor object to execute SQL queries
            cursor = conn.cursor()
            
            # Execute SQL SELECT to find user with matching username
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            # Fetch the user record from database
            user = cursor.fetchone()
            
            # Close the connection
            conn.close()
            
            # Check if user exists
            if user is None:
                # Return error if user not found
                return render_template('login.html', error='Username or password is incorrect!')
            
            # Hash the provided password and compare with stored hash
            # This verifies the password without storing plain text
            if hash_password(password) != user['password']:
                # Return error if password doesn't match
                return render_template('login.html', error='Username or password is incorrect!')
            
            # Create session for the logged-in user
            # session is a dictionary that persists across requests for this user
            session['user_id'] = user['id']
            # Store username in session for easy access in templates
            session['username'] = user['username']
            # Store user role in session (student or teacher)
            session['role'] = user['role']
            # Store full name in session
            session['full_name'] = user['full_name']
            
            # Update last_login timestamp in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
            conn.commit()
            conn.close()
            
            # Redirect to appropriate dashboard based on user role
            if user['role'] == 'teacher':
                # Teachers go to teacher dashboard
                return redirect(url_for('teacher_dashboard'))
            else:
                # Students go to student dashboard
                return redirect(url_for('student_dashboard'))
        
        except Exception as e:
            # Handle any unexpected database errors
            return render_template('login.html', error='An error occurred during login!')
    
    # If request is GET (display form)
    # Render the login form template
    return render_template('login.html')


# Define route for logout
@app.route("/logout")
def logout():
    """
    Clear user session and redirect to home page.
    
    Returns:
        Redirect to home page
    """
    # session.clear() removes all session data for the current user
    # This effectively logs them out
    session.clear()
    # Redirect to home page after logout
    return redirect(url_for('home'))


# Define route for student dashboard
@app.route("/student_dashboard")
def student_dashboard():
    """
    Display the student dashboard with enrolled courses and assignments.
    
    Only accessible to logged-in students.
    
    Returns:
        Rendered student dashboard template with courses and assignments
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'student'
    if session.get('role') != 'student':
        # Redirect to home if not a student (maybe a teacher)
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Fetch all courses the student is enrolled in
        cursor.execute("""
            SELECT c.id, c.title, c.description, c.teacher_id, u.full_name as teacher_name, e.progress
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            LEFT JOIN users u ON c.teacher_id = u.id
            WHERE e.student_id = ?
            ORDER BY c.created_at DESC
        """, (session['user_id'],))
        # Fetch all results
        enrolled_courses = cursor.fetchall()
        
        # Count available courses the student is NOT enrolled in
        cursor.execute("""
            SELECT COUNT(*) as count FROM courses
            WHERE id NOT IN (
                SELECT course_id FROM enrollments WHERE student_id = ?
            )
        """, (session['user_id'],))
        # Get the count
        available_courses_count = cursor.fetchone()['count']
        
        # Close connection
        conn.close()
        
        # Render student dashboard template with courses
        return render_template('student_dashboard.html', 
                             enrolled_courses=enrolled_courses,
                             available_courses_count=available_courses_count,
                             full_name=session.get('full_name'))
    
    except Exception as e:
        # Handle any database errors
        return render_template('student_dashboard.html', enrolled_courses=[], error='Error loading courses')


# Define route for teacher dashboard
@app.route("/teacher_dashboard")
def teacher_dashboard():
    """
    Display the teacher dashboard with created courses and student management.
    
    Only accessible to logged-in teachers.
    
    Returns:
        Rendered teacher dashboard template with courses and statistics
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'teacher'
    if session.get('role') != 'teacher':
        # Redirect to home if not a teacher (maybe a student)
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Fetch all courses created by this teacher
        cursor.execute("""
            SELECT id, title, description, created_at
            FROM courses
            WHERE teacher_id = ?
            ORDER BY created_at DESC
        """, (session['user_id'],))
        # Fetch all results
        my_courses = cursor.fetchall()
        
        # Count total students enrolled in this teacher's courses
        cursor.execute("""
            SELECT COUNT(DISTINCT e.student_id) as count
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE c.teacher_id = ?
        """, (session['user_id'],))
        # Get the count
        total_students = cursor.fetchone()['count']
        
        # Count total assignments (questions) created
        cursor.execute("""
            SELECT COUNT(m.id) as count
            FROM msqs m
            JOIN topics t ON m.topic_id = t.id
            JOIN courses c ON t.course_id = c.id
            WHERE c.teacher_id = ?
        """, (session['user_id'],))
        # Get the count
        total_assignments = cursor.fetchone()['count']
        
        # Pop one-time welcome message if present
        welcome = session.pop('welcome', None)

        # Render teacher dashboard template with statistics
        return render_template('teacher_dashboard.html',
                             my_courses=my_courses,
                             total_students=total_students,
                             total_assignments=total_assignments,
                             full_name=session.get('full_name'),
                             welcome=welcome)
    
    except Exception as e:
        # Handle any database errors
        return render_template('teacher_dashboard.html', my_courses=[], error='Error loading courses')


# Define route for admin dashboard
@app.route("/admin_dashboard")
def admin_dashboard():
    """
    Display the admin dashboard with user and course management.
    
    Only accessible to logged-in admins (teachers with admin role).
    
    Returns:
        Rendered admin dashboard template with user and course statistics
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'admin'
    if session.get('role') != 'teacher':
        # Redirect to home if not an admin (maybe a student)
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Count total registered users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users_count = cursor.fetchone()['count']
        
        # Count total courses available
        cursor.execute("SELECT COUNT(*) as count FROM courses")
        courses_count = cursor.fetchone()['count']
        
        # Fetch latest 10 users registered
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 10")
        users = cursor.fetchall()
        
        # Fetch latest 10 courses created
        cursor.execute("SELECT * FROM courses ORDER BY created_at DESC LIMIT 10")
        courses = cursor.fetchall()
        
        # Close connection
        conn.close()
        
        # Render admin dashboard template with statistics
        return render_template('admin_dashboard.html',
                             users_count=users_count,
                             courses_count=courses_count,
                             users=users,
                             courses=courses)
    except Exception as e:
        # Handle any database errors
        return render_template('admin_dashboard.html', error='Error loading admin data')


# Define route for course creation page (GET and POST)
@app.route("/create_course", methods=['GET', 'POST'])
def create_course():
    """
    Handle course creation for both GET (display form) and POST (process form).
    
    GET: Display course creation form
    POST: Process course creation form submission
    
    Returns:
        GET: Rendered course creation form template
        POST: Redirect to course management page on success or back to create course on error
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'teacher'
    if session.get('role') != 'teacher':
        # Redirect to home if not a teacher (maybe a student)
        return redirect(url_for('home'))
    
    # If request is POST (form submission)
    if request.method == 'POST':
        # Extract form data from the course creation form
        title = request.form.get('title')
        description = request.form.get('description')
        course_type = request.form.get('course_type', 'Self-Paced')
        duration = request.form.get('duration', 'Flexible')
        level = request.form.get('level', 'Beginner')
        
        # Validation: Check if course title is provided
        if not title:
            # Return error message if course title is empty
            return render_template('create_course.html', error='Course title is required!')
        
        if not description:
            # Return error message if description is empty
            return render_template('create_course.html', error='Course description is required!')
        
        try:
            # Establish connection to the database
            conn = get_db_connection()
            # Create cursor object to execute SQL commands
            cursor = conn.cursor()
            
            # Execute SQL INSERT to add new course to database with all fields
            cursor.execute("""
                INSERT INTO courses (title, description, course_type, duration, level, teacher_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, description, course_type, duration, level, session['user_id']))
            
            # Commit the changes to the database
            conn.commit()
            # Get the ID of the newly created course
            course_id = cursor.lastrowid
            # Close the connection
            conn.close()
            
            # Render success message and new course ID
            return render_template('create_course.html', 
                                 success='Course created successfully!',
                                 course_id=course_id)
        
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                return render_template('create_course.html', error='A course with this title already exists! Please use a different title.')
            else:
                return render_template('create_course.html', error='Database error. Please try again.')
        except Exception as e:
            return render_template('create_course.html', error=f'Error creating course: {str(e)}')
    
    # If request is GET (display form)
    # Render the course creation form template
    return render_template('create_course.html')


# Define route for course management page
@app.route("/manage_course/<int:course_id>", methods=['GET', 'POST'])
def manage_course(course_id):
    """
    Display and manage a specific course: view details, lessons, and assignments.
    
    Only accessible to the teacher who created the course.
    
    Args:
        course_id (int): ID of the course to manage
    
    Returns:
        Rendered course management template with course details, lessons, and assignments
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'teacher'
    if session.get('role') != 'teacher':
        # Redirect to home if not a teacher (maybe a student)
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Fetch the course details for the given course ID
        cursor.execute("""
            SELECT * FROM courses
            WHERE id = ? AND teacher_id = ?
        """, (course_id, session['user_id']))
        course = cursor.fetchone()
        
        # If course not found or doesn't belong to this teacher, show error
        if not course:
            return render_template('error.html', error='Course not found or unauthorized!')
        
        # Fetch all lessons (topics) for this course
        cursor.execute("""
            SELECT id, title, subtitle, created_at
            FROM topics
            WHERE course_id = ?
            ORDER BY created_at DESC
        """, (course_id,))
        lessons = cursor.fetchall()
        
        # Fetch all assignments (questions) for this course
        cursor.execute("""
            SELECT id, question, created_at
            FROM msqs
            WHERE topic_id IN (SELECT id FROM topics WHERE course_id = ?)
            ORDER BY created_at DESC
        """, (course_id,))
        questions = cursor.fetchall()
        
        # Fetch all assignment submissions (assignment metadata) for this course
        cursor.execute("""
            SELECT a.id, a.title, a.description, a.deadline,
                   COUNT(DISTINCT g.id) as graded_count,
                   COUNT(DISTINCT u.id) as total_students
            FROM assignments a
            LEFT JOIN grades g ON a.id = g.assignment_id
            LEFT JOIN (SELECT DISTINCT student_id FROM enrollments WHERE course_id = ?) u ON 1=1
            WHERE a.course_id = ?
            GROUP BY a.id
            ORDER BY a.id DESC
        """, (course_id, course_id))
        assignments = cursor.fetchall()
        
        # Close connection
        conn.close()
        
        # Render course management template with course details, lessons, and assignments
        return render_template('manage_course.html',
                             course=course,
                             lessons=lessons,
                             assignments=assignments,
                             questions=questions)
    
    except Exception as e:
        # Handle any database errors
        return render_template('error.html', error='Error loading course!')


# Define route for lesson creation page
@app.route("/create_lesson/<int:course_id>", methods=['GET', 'POST'])
def create_lesson(course_id):
    """
    Handle lesson creation for both GET (display form) and POST (process form).
    
    GET: Display lesson creation form
    POST: Process lesson creation form submission
    
    Args:
        course_id (int): ID of the course to create lesson for
    
    Returns:
        GET: Rendered lesson creation form template
        POST: Redirect to course management page on success or back to create lesson on error
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'teacher'
    if session.get('role') != 'teacher':
        # Redirect to home if not a teacher (maybe a student)
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Fetch the course details for the given course ID
        cursor.execute("""
            SELECT * FROM courses
            WHERE id = ? AND teacher_id = ?
        """, (course_id, session['user_id']))
        course = cursor.fetchone()
        
        # If course not found or doesn't belong to this teacher, show error
        if not course:
            return render_template('error.html', error='Course not found or unauthorized!')
        
        # If request is POST (form submission)
        if request.method == 'POST':
            # Extract form data from the lesson creation form
            title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            content = request.form.get('content')
            
            # Validation: Check if lesson title is provided
            if not title:
                # Return error message if lesson title is empty
                return render_template('create_lesson.html', course=course, error='Lesson title is required!')
            
            # Execute SQL INSERT to add new lesson (topic) to database
            cursor.execute("""
                INSERT INTO topics (course_id, title, subtitle, content)
                VALUES (?, ?, ?, ?)
            """, (course_id, title, subtitle, content))
            
            # Get the lesson ID that was just created
            lesson_id = cursor.lastrowid
            
            # Fetch all students enrolled in the course to notify them
            cursor.execute("""
                SELECT student_id FROM enrollments WHERE course_id = ?
            """, (course_id,))
            
            students = cursor.fetchall()
            
            # Create notifications for all enrolled students
            try:
                for student in students:
                    cursor.execute("""
                        INSERT INTO notifications (student_id, course_id, notification_type, title, message, resource_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (student['student_id'], course_id, 'lesson', 
                          f"New Lesson: {title}", 
                          f"A new lesson '{title}' has been added to the course.",
                          lesson_id))
                print(f"Created notifications for {len(students)} enrolled students in lesson '{title}'")
            except Exception as notif_error:
                print(f"Error creating notifications: {str(notif_error)}")
            
            # Commit the changes to the database
            conn.commit()
            # Close the connection
            conn.close()
            
            # Render success message
            return render_template('create_lesson.html', 
                                 course=course,
                                 success='Lesson created successfully!')
        
        # If request is GET (display form)
        # Render the lesson creation form template
        conn.close()
        return render_template('create_lesson.html', course=course)
    
    except Exception as e:
        # Handle any unexpected errors
        print(f"Error in create_lesson: {str(e)}")
        return render_template('error.html', error=f'Error creating lesson: {str(e)}')


# Define route for editing a lesson
@app.route("/edit_lesson/<int:lesson_id>", methods=['GET', 'POST'])
def edit_lesson(lesson_id):
    """
    Handle lesson editing for both GET (display form) and POST (process form).
    
    GET: Display lesson editing form
    POST: Process lesson editing form submission
    
    Args:
        lesson_id (int): ID of the lesson/topic to edit
    
    Returns:
        GET: Rendered lesson editing form template
        POST: Redirect to course management page on success or back to edit on error
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user role is 'teacher'
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch the lesson details
        cursor.execute("""
            SELECT t.*, c.id as course_id 
            FROM topics t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.id = ?
        """, (lesson_id,))
        
        lesson = cursor.fetchone()
        
        if not lesson:
            conn.close()
            return render_template('error.html', error='Lesson not found!')
        
        # Verify teacher owns this course
        cursor.execute("""
            SELECT id FROM courses WHERE id = ? AND teacher_id = ?
        """, (lesson['course_id'], session['user_id']))
        
        if not cursor.fetchone():
            conn.close()
            return render_template('error.html', error='Unauthorized!')
        
        # If request is POST (form submission)
        if request.method == 'POST':
            title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            content = request.form.get('content')
            
            if not title:
                return render_template('edit_lesson.html', lesson=lesson, error='Lesson title is required!')
            
            # Update the lesson in database
            cursor.execute("""
                UPDATE topics 
                SET title = ?, subtitle = ?, content = ?
                WHERE id = ?
            """, (title, subtitle, content, lesson_id))
            
            conn.commit()
            conn.close()
            
            return render_template('edit_lesson.html', 
                                 lesson=lesson,
                                 success='Lesson updated successfully!')
        
        conn.close()
        return render_template('edit_lesson.html', lesson=lesson)
    
    except Exception as e:
        return render_template('error.html', error='Error editing lesson!')


# Define route for deleting a lesson
@app.route("/delete_lesson/<int:lesson_id>", methods=['POST'])
def delete_lesson(lesson_id):
    """
    Delete a lesson/topic from the database.
    
    Args:
        lesson_id (int): ID of the lesson to delete
    
    Returns:
        Redirect to manage_course page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a teacher
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch the lesson to get course_id
        cursor.execute("""
            SELECT course_id FROM topics WHERE id = ?
        """, (lesson_id,))
        
        lesson = cursor.fetchone()
        if not lesson:
            conn.close()
            return redirect(url_for('teacher_dashboard'))
        
        course_id = lesson['course_id']
        
        # Verify teacher owns this course
        cursor.execute("""
            SELECT id FROM courses WHERE id = ? AND teacher_id = ?
        """, (course_id, session['user_id']))
        
        if not cursor.fetchone():
            conn.close()
            return render_template('error.html', error='Unauthorized!')
        
        # Delete all submissions for questions in this lesson
        cursor.execute("""
            DELETE FROM submissions 
            WHERE question_id IN (
                SELECT id FROM msqs WHERE topic_id = ?
            )
        """, (lesson_id,))
        
        # Delete all questions for this lesson
        cursor.execute("""
            DELETE FROM msqs WHERE topic_id = ?
        """, (lesson_id,))
        
        # Delete the lesson
        cursor.execute("""
            DELETE FROM topics WHERE id = ?
        """, (lesson_id,))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('manage_course', course_id=course_id))
    
    except Exception as e:
        return render_template('error.html', error='Error deleting lesson!')


# Define route for deleting an assignment/question
@app.route("/delete_assignment/<int:assignment_id>", methods=['POST'])
def delete_assignment(assignment_id):
    """
    Delete an assignment/question from the database.
    
    Args:
        assignment_id (int): ID of the assignment to delete
    
    Returns:
        Redirect to manage_course page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a teacher
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch the assignment and get course_id through topic
        cursor.execute("""
            SELECT m.id, t.course_id 
            FROM msqs m
            LEFT JOIN topics t ON m.topic_id = t.id
            WHERE m.id = ?
        """, (assignment_id,))
        
        assignment = cursor.fetchone()
        if not assignment:
            conn.close()
            return redirect(url_for('teacher_dashboard'))
        
        course_id = assignment['course_id']
        
        # Verify teacher owns this course
        cursor.execute("""
            SELECT id FROM courses WHERE id = ? AND teacher_id = ?
        """, (course_id, session['user_id']))
        
        if not cursor.fetchone():
            conn.close()
            return render_template('error.html', error='Unauthorized!')
        
        # Delete all submissions for this question
        cursor.execute("""
            DELETE FROM submissions WHERE question_id = ?
        """, (assignment_id,))
        
        # Delete the question/assignment
        cursor.execute("""
            DELETE FROM msqs WHERE id = ?
        """, (assignment_id,))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('manage_course', course_id=course_id))
    
    except Exception as e:
        return render_template('error.html', error='Error deleting assignment!')


# Define route for assignment creation page
@app.route("/create_assignment/<int:course_id>", methods=['GET', 'POST'])
def create_assignment(course_id):
    """
    Handle assignment creation for both GET (display form) and POST (process form).
    
    GET: Display assignment creation form
    POST: Process assignment creation form submission
    
    Args:
        course_id (int): ID of the course to create assignment for
    
    Returns:
        GET: Rendered assignment creation form template
        POST: Redirect to course management page on success or back to create assignment on error
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'teacher'
    if session.get('role') != 'teacher':
        # Redirect to home if not a teacher (maybe a student)
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Fetch the course details for the given course ID
        cursor.execute("""
            SELECT * FROM courses
            WHERE id = ? AND teacher_id = ?
        """, (course_id, session['user_id']))
        course = cursor.fetchone()
        
        # If course not found or doesn't belong to this teacher, show error
        if not course:
            return render_template('error.html', error='Course not found or unauthorized!')
        
        # Fetch all topics (lessons) for this course
        cursor.execute("""
            SELECT id, title FROM topics
            WHERE course_id = ?
            ORDER BY created_at DESC
        """, (course_id,))
        topics = cursor.fetchall()
        
        # If request is POST (form submission)
        if request.method == 'POST':
            # Extract form data from the assignment creation form
            topic_id = request.form.get('topic_id')
            new_topic_title = request.form.get('new_topic_title')
            new_topic_subtitle = request.form.get('new_topic_subtitle')
            question = request.form.get('question')
            option_a = request.form.get('option_a')
            option_b = request.form.get('option_b')
            option_c = request.form.get('option_c')
            option_d = request.form.get('option_d')
            correct_answer = request.form.get('correct_answer')

            # Allow creating a new topic inline: require either an existing topic or a new topic title
            if not (topic_id or (new_topic_title and new_topic_title.strip())):
                return render_template('create_assignment.html', course=course, topics=topics, error='Please select a topic or enter a new topic title!')

            # Validation: Check if required assignment fields are filled
            if not all([question, option_a, option_b, option_c, option_d, correct_answer]):
                return render_template('create_assignment.html', course=course, topics=topics, error='All fields are required!')

            # If new topic title provided, create the topic and use its id
            if new_topic_title and new_topic_title.strip():
                cursor.execute("""
                    INSERT INTO topics (course_id, title, subtitle)
                    VALUES (?, ?, ?)
                """, (course_id, new_topic_title.strip(), new_topic_subtitle))
                conn.commit()
                topic_id = cursor.lastrowid

                # Refresh topics list so the new topic appears in the dropdown
                cursor.execute("""
                    SELECT id, title FROM topics
                    WHERE course_id = ?
                    ORDER BY created_at DESC
                """, (course_id,))
                topics = cursor.fetchall()

            # Ensure topic_id is an int
            try:
                topic_id = int(topic_id)
            except Exception:
                return render_template('create_assignment.html', course=course, topics=topics, error='Invalid topic selected')

            # Execute SQL INSERT to add new assignment (question) to database
            cursor.execute("""
                INSERT INTO msqs (topic_id, question, option_a, option_b, option_c, option_d, correct_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (topic_id, question, option_a, option_b, option_c, option_d, correct_answer))
            
            # Get the assignment ID that was just created
            assignment_id = cursor.lastrowid
            
            # Fetch all students enrolled in the course to notify them
            cursor.execute("""
                SELECT student_id FROM enrollments WHERE course_id = ?
            """, (course_id,))
            
            students = cursor.fetchall()
            
            # Create notifications for all enrolled students
            try:
                for student in students:
                    cursor.execute("""
                        INSERT INTO notifications (student_id, course_id, notification_type, title, message, resource_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (student['student_id'], course_id, 'assignment', 
                          f"New Assignment: {question[:50]}...", 
                          f"A new assignment has been added: {question[:80]}",
                          assignment_id))
                print(f"Created notifications for {len(students)} enrolled students in assignment: {question[:50]}...")
            except Exception as notif_error:
                print(f"Error creating assignment notifications: {str(notif_error)}")

            # Commit the changes to the database
            conn.commit()
            # Close the connection
            conn.close()

            # Render success message and select the topic that was used
            return render_template('create_assignment.html', course=course, topics=topics, success='Assignment created successfully!', selected_topic_id=topic_id)
        
        # If request is GET (display form)
        # Render the assignment creation form template
        conn.close()
        return render_template('create_assignment.html', course=course, topics=topics)
    
    except Exception as e:
        # Handle any unexpected errors
        print(f"Error in create_assignment: {str(e)}")
        return render_template('error.html', error=f'Error creating assignment: {str(e)}')


# Define route for lessons page
@app.route("/lessons")
def lessons():
    """
    Render the lessons page with all available topics/lessons.
    
    Fetches lesson data from topics table joined with courses table.
    
    Returns:
        Rendered HTML template with lessons data
    """
    try:
        # Try to fetch lessons from database
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Execute SQL query to fetch all lessons with related course information
        # SELECT: Choose which columns to fetch
        # t.id, t.title, t.subtitle: Get topic ID, title, and subtitle
        # c.title as course_title: Get course title and alias it as course_title
        # FROM topics t: Select from topics table, alias it as 't'
        # LEFT JOIN courses c: Join with courses table to get course info
        # ON t.course_id = c.id: Join condition - match topic's course_id with course's id
        # ORDER BY t.id DESC: Sort results by topic ID in descending order (newest first)
        cursor.execute("""
            SELECT t.id, t.title, t.subtitle, c.title as course_title 
            FROM topics t 
            LEFT JOIN courses c ON t.course_id = c.id
            ORDER BY t.id DESC
        """)
        # Fetch all results from the query and store in lessons_data list
        lessons_data = cursor.fetchall()
        # Close the database connection to free resources
        conn.close()
    except sqlite3.OperationalError:
        # If topics table doesn't exist, return empty list
        lessons_data = []
    
    # Render lessons.html template and pass lessons data as variable
    # The template can loop through this data with {% for lesson in lessons %}
    return render_template('lessons.html', lessons=lessons_data)


# Define route for viewing a specific lesson
@app.route("/lesson/<int:lesson_id>")
def view_lesson(lesson_id):
    """
    Display a specific lesson with its content and details.
    
    Args:
        lesson_id (int): ID of the lesson/topic to view
    
    Returns:
        Rendered lesson detail page
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch the specific lesson details
        cursor.execute("""
            SELECT t.id, t.title, t.subtitle, t.content, c.id as course_id, c.title as course_title
            FROM topics t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.id = ?
        """, (lesson_id,))
        
        lesson = cursor.fetchone()
        
        if not lesson:
            conn.close()
            return render_template('error.html', error='Lesson not found!')
        
        # Fetch all questions/assignments for this lesson
        cursor.execute("""
            SELECT id, question, option_a, option_b, option_c, option_d, correct_answer
            FROM msqs
            WHERE topic_id = ?
            ORDER BY id ASC
        """, (lesson_id,))
        
        questions = cursor.fetchall()
        conn.close()
        
        return render_template('lesson_detail.html', 
                             lesson=lesson,
                             questions=questions)
    
    except Exception as e:
        return render_template('error.html', error='Error loading lesson!')


# Define route for courses page
@app.route("/course")
def course():
    """
    Render the courses page with all available courses.
    Shows enrolled courses if student is logged in, otherwise shows all courses.
    
    Returns:
        Rendered HTML template with courses data
    """
    enrolled_courses = []
    all_courses = []
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all courses
        cursor.execute("""
            SELECT c.id, c.title, c.description, c.course_id, u.full_name as teacher_name
            FROM courses c
            LEFT JOIN users u ON c.teacher_id = u.id
            ORDER BY c.id DESC
        """)
        all_courses = cursor.fetchall()
        
        # If student is logged in, get their enrolled courses
        if user_id and user_role == 'student':
            cursor.execute("""
                SELECT c.id, c.title, c.description, c.course_id, u.full_name as teacher_name, 
                       e.progress, e.enrolled_at
                FROM courses c
                LEFT JOIN users u ON c.teacher_id = u.id
                LEFT JOIN enrollments e ON c.id = e.course_id
                WHERE e.student_id = ? AND e.student_id IS NOT NULL
                ORDER BY c.id DESC
            """, (user_id,))
            enrolled_courses = cursor.fetchall()
        
        conn.close()
    except sqlite3.OperationalError:
        pass
    
    return render_template('course.html', 
                         all_courses=all_courses,
                         enrolled_courses=enrolled_courses,
                         is_logged_in=user_id is not None,
                         is_student=user_role == 'student')


# Define route for learning a specific course (student view)
@app.route("/learn/<int:course_id>")
def learn_course(course_id):
    """
    Display course learning page for a student with all lessons and assignments.
    
    Shows:
    - Course details (title, description, instructor)
    - Progress tracking
    - All lessons in the course with links
    - All assignments for the course
    - Course materials
    
    Args:
        course_id (int): ID of the course to learn
    
    Returns:
        Rendered course learning page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a student
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch course details
        cursor.execute("""
            SELECT c.id, c.title, c.description, c.level, c.duration, 
                   u.full_name as teacher_name, c.course_type
            FROM courses c
            LEFT JOIN users u ON c.teacher_id = u.id
            WHERE c.id = ?
        """, (course_id,))
        
        course = cursor.fetchone()
        
        if not course:
            conn.close()
            return render_template('error.html', error='Course not found!')
        
        # Check if student is enrolled in this course
        cursor.execute("""
            SELECT progress FROM enrollments
            WHERE student_id = ? AND course_id = ?
        """, (session['user_id'], course_id))
        
        enrollment = cursor.fetchone()
        
        if not enrollment:
            conn.close()
            return render_template('error.html', error='You are not enrolled in this course!')
        
        # Fetch all lessons/topics for this course
        cursor.execute("""
            SELECT id, title, subtitle, content, created_at
            FROM topics
            WHERE course_id = ?
            ORDER BY created_at ASC
        """, (course_id,))
        
        lessons = cursor.fetchall()
        
        # Fetch all assignments/questions for this course
        cursor.execute("""
            SELECT m.id, m.question, m.correct_answer, t.id as topic_id, t.title as topic_title
            FROM msqs m
            LEFT JOIN topics t ON m.topic_id = t.id
            WHERE t.course_id = ?
            ORDER BY t.created_at ASC, m.id ASC
        """, (course_id,))
        
        assignments = cursor.fetchall()
        
        # Count student's correct submissions for this course
        cursor.execute("""
            SELECT COUNT(*) as total_correct
            FROM submissions s
            JOIN msqs m ON s.question_id = m.id
            JOIN topics t ON m.topic_id = t.id
            WHERE s.student_id = ? AND t.course_id = ? AND s.is_correct = 1
        """, (session['user_id'], course_id))
        
        stats = cursor.fetchone()
        correct_submissions = stats['total_correct'] if stats else 0
        
        conn.close()
        
        return render_template('learn_course.html',
                             course=course,
                             lessons=lessons,
                             assignments=assignments,
                             progress=enrollment['progress'],
                             correct_submissions=correct_submissions,
                             total_assignments=len(assignments))
    
    except Exception as e:
        return render_template('error.html', error='Error loading course!')


# Define route for assignments page
@app.route("/assignments")
def assignments():
    """
    Render the assignments page with quiz questions.
    
    Fetches multiple choice questions from msqs table with related topic info.
    
    Returns:
        Rendered HTML template with assignments data
    """
    try:
        # Try to fetch assignments from database
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Execute SQL query to fetch all multiple choice questions
        # SELECT m.id: Get question ID
        # m.question: Get the question text
        # t.title as topic_title: Get topic title and alias as topic_title
        # m.option_a, m.option_b, m.option_c, m.option_d: Get all answer options
        # FROM msqs m: Select from msqs (multiple choice questions) table, alias as 'm'
        # LEFT JOIN topics t: Join with topics table to get topic info
        # ON m.topic_id = t.id: Join condition - match question's topic_id with topic's id
        # ORDER BY m.id DESC: Sort by question ID in descending order (newest first)
        # LIMIT 20: Fetch only the first 20 questions
        cursor.execute("""
            SELECT m.id, m.question, t.title as topic_title, 
                   m.option_a, m.option_b, m.option_c, m.option_d
            FROM msqs m 
            LEFT JOIN topics t ON m.topic_id = t.id
            ORDER BY m.id DESC
            LIMIT 20
        """)
        # Fetch all results from the query and store in assignments_data list
        assignments_data = cursor.fetchall()
        # Close the database connection to free resources
        conn.close()
    except sqlite3.OperationalError:
        # If msqs table doesn't exist, return empty list
        assignments_data = []
    
    # Render assignments.html template and pass assignments data as variable
    # The template can loop through this data with {% for assignment in assignments %}
    return render_template('assignments.html', assignments=assignments_data)


# Define route for enrolling in a course
@app.route("/enroll/<int:course_id>")
def enroll_course(course_id):
    """
    Enroll a student in a course.
    
    Args:
        course_id (int): ID of the course to enroll in
    
    Returns:
        Redirect to student dashboard
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'student'
    if session.get('role') != 'student':
        # Redirect to home if not a student (maybe a teacher)
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL commands
        cursor = conn.cursor()
        
        # Execute SQL INSERT to add new enrollment record
        cursor.execute("""
            INSERT INTO enrollments (student_id, course_id)
            VALUES (?, ?)
        """, (session['user_id'], course_id))
        
        # Commit the changes to the database
        conn.commit()
        # Close the connection
        conn.close()
    except sqlite3.IntegrityError:
        # Handle case where enrollment already exists (duplicate key)
        pass
    
    # Redirect to student dashboard after enrolling
    return redirect(url_for('student_dashboard'))


# Define route for marking attendance for a lesson
@app.route("/mark_attendance/<int:lesson_id>", methods=['GET', 'POST'])
def mark_attendance(lesson_id):
    """
    Mark attendance for students in a lesson.
    
    GET: Display attendance form with list of enrolled students
    POST: Save attendance records to database
    
    Args:
        lesson_id (int): ID of the lesson
    
    Returns:
        Rendered attendance form or redirect to manage_course
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a teacher
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get lesson details and verify teacher owns it
        cursor.execute("""
            SELECT t.id, t.title, t.course_id, c.id as course_check
            FROM topics t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.id = ? AND c.teacher_id = ?
        """, (lesson_id, session['user_id']))
        
        lesson = cursor.fetchone()
        
        if not lesson:
            conn.close()
            return render_template('error.html', error='Lesson not found or unauthorized!')
        
        course_id = lesson['course_id']
        
        if request.method == 'POST':
            # Get form data for all students
            attendance_data = request.form.to_dict()
            
            # Process each student
            for key, value in attendance_data.items():
                if key.startswith('attendance_'):
                    try:
                        student_id = int(key.split('_')[1])
                        status = value  # 'present', 'absent', 'late'
                        
                        # Check if attendance record exists for today
                        cursor.execute("""
                            SELECT id FROM attendance
                            WHERE student_id = ? AND lesson_id = ? AND DATE(lesson_date) = DATE('now')
                        """, (student_id, lesson_id))
                        
                        existing = cursor.fetchone()
                        
                        if existing:
                            # Update existing record
                            cursor.execute("""
                                UPDATE attendance
                                SET status = ?
                                WHERE student_id = ? AND lesson_id = ? AND DATE(lesson_date) = DATE('now')
                            """, (status, student_id, lesson_id))
                        else:
                            # Insert new record
                            cursor.execute("""
                                INSERT INTO attendance (student_id, lesson_id, course_id, status)
                                VALUES (?, ?, ?, ?)
                            """, (student_id, lesson_id, course_id, status))
                    except (ValueError, IndexError):
                        continue
            
            conn.commit()
            conn.close()
            
            return redirect(url_for('manage_course', course_id=course_id))
        
        # GET: Fetch all students enrolled in the course
        cursor.execute("""
            SELECT DISTINCT u.id, u.full_name, e.student_id
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.course_id = ? AND u.role = 'student'
            ORDER BY u.full_name
        """, (course_id,))
        
        students = cursor.fetchall()
        
        # Fetch today's attendance records for this lesson
        cursor.execute("""
            SELECT student_id, status FROM attendance
            WHERE lesson_id = ? AND DATE(lesson_date) = DATE('now')
        """, (lesson_id,))
        
        attendance_records = {row['student_id']: row['status'] for row in cursor.fetchall()}
        
        conn.close()
        
        return render_template('mark_attendance.html',
                             lesson=lesson,
                             students=students,
                             attendance_records=attendance_records,
                             course_id=course_id)
    
    except Exception as e:
        return render_template('error.html', error='Error marking attendance!')


# Define route for viewing attendance reports
@app.route("/attendance/<int:course_id>")
def view_attendance(course_id):
    """
    View attendance report for a course.
    
    Shows attendance records for all students and lessons in the course.
    
    Args:
        course_id (int): ID of the course
    
    Returns:
        Rendered attendance report page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a teacher
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify teacher owns this course
        cursor.execute("""
            SELECT id, title FROM courses WHERE id = ? AND teacher_id = ?
        """, (course_id, session['user_id']))
        
        course = cursor.fetchone()
        
        if not course:
            conn.close()
            return render_template('error.html', error='Course not found or unauthorized!')
        
        # Get all students enrolled in the course
        cursor.execute("""
            SELECT DISTINCT u.id, u.full_name
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.course_id = ? AND u.role = 'student'
            ORDER BY u.full_name
        """, (course_id,))
        
        students = cursor.fetchall()
        
        # Get all lessons in the course
        cursor.execute("""
            SELECT id, title FROM topics WHERE course_id = ? ORDER BY created_at ASC
        """, (course_id,))
        
        lessons = cursor.fetchall()
        
        # Get all attendance records
        cursor.execute("""
            SELECT student_id, lesson_id, status, lesson_date
            FROM attendance
            WHERE course_id = ?
            ORDER BY lesson_date DESC
        """, (course_id,))
        
        attendance_records = cursor.fetchall()
        
        # Organize attendance data for easy access
        attendance_data = {}
        for record in attendance_records:
            key = (record['student_id'], record['lesson_id'])
            attendance_data[key] = record['status']
        
        conn.close()
        
        return render_template('attendance_report.html',
                             course=course,
                             students=students,
                             lessons=lessons,
                             attendance_data=attendance_data)
    
    except Exception as e:
        return render_template('error.html', error='Error loading attendance report!')


# Define route for submitting assignment answers
@app.route("/submit_assignment", methods=['POST'])
def submit_assignment():
    """
    Handle assignment submission from students.
    
    Processes the form data from assignments.html form submission,
    validates answers, saves submissions to the database, and redirects to results page.
    
    Returns:
        Redirect to assignment results page or back to assignments on error
    """
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' not in session:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
    
    # Check if user role is 'student'
    if session.get('role') != 'student':
        # Redirect to home if not a student
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all form data from the submission
        form_data = request.form.to_dict()
        
        # Track submission statistics
        total_correct = 0
        total_questions = 0
        submission_ids = []
        
        # Process each question submission
        for key, value in form_data.items():
            # Form key format: question_<question_id>
            if key.startswith('question_'):
                try:
                    # Extract question ID from form key
                    question_id = int(key.split('_')[1])
                    selected_answer = value.upper() if value else None
                    
                    if not selected_answer or selected_answer not in ['A', 'B', 'C', 'D']:
                        # Skip invalid answers
                        continue
                    
                    # Fetch the correct answer for this question
                    cursor.execute("""
                        SELECT correct_answer FROM msqs WHERE id = ?
                    """, (question_id,))
                    
                    result = cursor.fetchone()
                    if not result:
                        # Skip if question not found
                        continue
                    
                    correct_answer = result['correct_answer'].upper()
                    # Determine if answer is correct
                    is_correct = 1 if selected_answer == correct_answer else 0
                    
                    # Insert submission record into database
                    cursor.execute("""
                        INSERT INTO submissions (student_id, question_id, selected_answer, is_correct)
                        VALUES (?, ?, ?, ?)
                    """, (session['user_id'], question_id, selected_answer, is_correct))
                    
                    # Track for statistics
                    submission_ids.append(cursor.lastrowid)
                    if is_correct:
                        total_correct += 1
                    total_questions += 1
                    
                except (ValueError, IndexError):
                    # Skip malformed form keys
                    continue
        
        # Commit all submissions to database
        conn.commit()
        
        # Calculate percentage score
        percentage_score = int((total_correct / total_questions * 100)) if total_questions > 0 else 0
        
        # Close the connection
        conn.close()
        
        # Redirect to results page with statistics
        return redirect(url_for('assignment_results', 
                              correct=total_correct, 
                              total=total_questions,
                              percentage=percentage_score))
    
    except Exception as e:
        # Log error and redirect back to assignments
        return redirect(url_for('assignments'))


# Define route for viewing assignment results
@app.route("/assignment_results")
def assignment_results():
    """
    Display the results of a student's assignment submission.
    
    Shows score, number correct, total questions, and percentage.
    
    Returns:
        Rendered results template with score information
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get query parameters for results
    correct = request.args.get('correct', 0, type=int)
    total = request.args.get('total', 0, type=int)
    percentage = request.args.get('percentage', 0, type=int)
    
    # Determine performance level
    if percentage >= 80:
        performance = "Excellent! 🌟"
        performance_color = "#28a745"  # Green
    elif percentage >= 60:
        performance = "Good! 👍"
        performance_color = "#ffc107"  # Yellow
    else:
        performance = "Keep Practicing! 💪"
        performance_color = "#dc3545"  # Red
    
    return render_template('assignment_results.html',
                         correct=correct,
                         total=total,
                         percentage=percentage,
                         performance=performance,
                         performance_color=performance_color)


# Define route for viewing student's assignment submissions and grades
@app.route("/my_assignments")
def my_assignments():
    """
    Display all assignments completed by the logged-in student with their scores.
    
    Shows a list of all assignments the student has submitted with:
    - Question text
    - Student's selected answer
    - Correct answer
    - Whether they got it right
    - Date submitted
    
    Returns:
        Rendered my_assignments template with student's submission history
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user role is 'student'
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    
    try:
        # Establish connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch all submissions by this student with question details
        cursor.execute("""
            SELECT 
                s.id as submission_id,
                s.question_id,
                s.selected_answer,
                s.is_correct,
                s.submitted_at,
                m.question,
                m.correct_answer,
                m.option_a,
                m.option_b,
                m.option_c,
                m.option_d,
                t.title as topic_title
            FROM submissions s
            JOIN msqs m ON s.question_id = m.id
            LEFT JOIN topics t ON m.topic_id = t.id
            WHERE s.student_id = ?
            ORDER BY s.submitted_at DESC
        """, (session['user_id'],))
        
        submissions = cursor.fetchall()
        
        # Calculate overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_submissions,
                SUM(is_correct) as correct_answers
            FROM submissions
            WHERE student_id = ?
        """, (session['user_id'],))
        
        stats = cursor.fetchone()
        total_submissions = stats['total_submissions'] if stats['total_submissions'] else 0
        correct_answers = stats['correct_answers'] if stats['correct_answers'] else 0
        overall_percentage = int((correct_answers / total_submissions * 100)) if total_submissions > 0 else 0
        
        conn.close()
        
        return render_template('my_assignments.html',
                             submissions=submissions,
                             total_submissions=total_submissions,
                             correct_answers=correct_answers,
                             overall_percentage=overall_percentage)
    
    except Exception as e:
        return render_template('error.html', error='Error loading your assignments!')


# Define route for viewing assignment submissions for grading
@app.route("/grade_assignment/<int:assignment_id>")
def grade_assignment(assignment_id):
    """
    Display all student submissions for an assignment that the teacher created.
    
    Shows a list of all students who submitted the assignment with their submission status.
    
    Args:
        assignment_id (int): ID of the assignment to view submissions for
    
    Returns:
        Rendered grade_assignment template with submission list
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a teacher
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get assignment details
        cursor.execute("""
            SELECT a.*, c.title as course_title
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
            WHERE a.id = ? AND c.teacher_id = ?
        """, (assignment_id, session['user_id']))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            return render_template('error.html', error='Assignment not found or unauthorized!')
        
        # Get all students in the course
        cursor.execute("""
            SELECT DISTINCT u.id, u.full_name, u.username
            FROM users u
            WHERE u.role = 'student'
            ORDER BY u.full_name
        """)
        
        all_students = cursor.fetchall()
        
        # Get grades for each student
        grades_by_student = {}
        for student in all_students:
            cursor.execute("""
                SELECT grade, feedback, graded_at
                FROM grades
                WHERE student_id = ? AND assignment_id = ?
            """, (student['id'], assignment_id))
            grade = cursor.fetchone()
            grades_by_student[student['id']] = grade
        
        conn.close()
        
        return render_template('grade_assignment.html',
                             assignment=assignment,
                             students=all_students,
                             grades=grades_by_student)
    
    except Exception as e:
        return render_template('error.html', error=f'Error loading assignment: {str(e)}')


# Define route for grading a specific student submission
@app.route("/submit_grade/<int:assignment_id>/<int:student_id>", methods=['GET', 'POST'])
def submit_grade(assignment_id, student_id):
    """
    Display grading form and process grade submission for a student's assignment.
    
    GET: Display the grading form with current submission details and any existing grade
    POST: Process the grade and feedback submission
    
    Args:
        assignment_id (int): ID of the assignment being graded
        student_id (int): ID of the student being graded
    
    Returns:
        GET: Rendered grading form
        POST: Redirect to grade_assignment page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a teacher
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify assignment exists and belongs to this teacher
        cursor.execute("""
            SELECT a.*, c.title as course_title
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
            WHERE a.id = ? AND c.teacher_id = ?
        """, (assignment_id, session['user_id']))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            return render_template('error.html', error='Assignment not found or unauthorized!')
        
        # Get student details
        cursor.execute("SELECT * FROM users WHERE id = ? AND role = 'student'", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            return render_template('error.html', error='Student not found!')
        
        # Get existing grade if any
        cursor.execute("""
            SELECT * FROM grades
            WHERE student_id = ? AND assignment_id = ?
        """, (student_id, assignment_id))
        
        existing_grade = cursor.fetchone()
        
        if request.method == 'POST':
            # Get grade and feedback from form
            grade = request.form.get('grade', type=float)
            feedback = request.form.get('feedback', '')
            
            # Validate grade
            if grade is None or grade < 0 or grade > 100:
                return render_template('grade_submission.html',
                                     assignment=assignment,
                                     student=student,
                                     existing_grade=existing_grade,
                                     error='Grade must be between 0 and 100!')
            
            # Check if grade already exists
            if existing_grade:
                # Update existing grade
                cursor.execute("""
                    UPDATE grades
                    SET grade = ?, feedback = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE student_id = ? AND assignment_id = ?
                """, (grade, feedback, student_id, assignment_id))
            else:
                # Insert new grade
                cursor.execute("""
                    INSERT INTO grades (student_id, assignment_id, teacher_id, grade, feedback)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_id, assignment_id, session['user_id'], grade, feedback))
            
            conn.commit()
            conn.close()
            
            # Redirect back to assignment grading page
            return redirect(url_for('grade_assignment', assignment_id=assignment_id))
        
        # GET request - show the grading form
        conn.close()
        
        return render_template('grade_submission.html',
                             assignment=assignment,
                             student=student,
                             existing_grade=existing_grade)
    
    except Exception as e:
        return render_template('error.html', error=f'Error processing grade: {str(e)}')


# Define route for viewing student's grades
@app.route("/student_grades")
def student_grades():
    """
    Display all grades received by the logged-in student for assignments.
    
    Shows a list of all grades with feedback from teachers.
    
    Returns:
        Rendered student_grades template with grade information
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a student
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch all grades for this student
        cursor.execute("""
            SELECT 
                g.id,
                g.grade,
                g.feedback,
                g.graded_at,
                a.title as assignment_title,
                a.id as assignment_id,
                c.title as course_title,
                u.full_name as teacher_name
            FROM grades g
            JOIN assignments a ON g.assignment_id = a.id
            JOIN courses c ON a.course_id = c.id
            JOIN users u ON g.teacher_id = u.id
            WHERE g.student_id = ?
            ORDER BY g.graded_at DESC
        """, (session['user_id'],))
        
        grades = cursor.fetchall()
        
        # Calculate statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_graded,
                AVG(grade) as average_grade
            FROM grades
            WHERE student_id = ?
        """, (session['user_id'],))
        
        stats = cursor.fetchone()
        total_graded = stats['total_graded'] if stats['total_graded'] else 0
        average_grade = round(stats['average_grade'], 2) if stats['average_grade'] else 0
        
        conn.close()
        
        return render_template('student_grades.html',
                             grades=grades,
                             total_graded=total_graded,
                             average_grade=average_grade)
    
    except Exception as e:
        return render_template('error.html', error=f'Error loading grades: {str(e)}')


# Define route for viewing notifications
@app.route("/notifications")
def notifications():
    """
    Display notifications:
    - For students: Show notifications they've received from teachers
    - For teachers: Show notifications they've sent to students
    
    Returns:
        Rendered notifications page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role')
    user_id = session['user_id']
    
    # Reject unauthorized users
    if user_role not in ['student', 'teacher']:
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_role == 'student':
            # For students: Show notifications they've received
            cursor.execute("""
                SELECT n.*, c.title as course_title
                FROM notifications n
                LEFT JOIN courses c ON n.course_id = c.id
                WHERE n.student_id = ?
                ORDER BY n.created_at DESC
            """, (user_id,))
            
            all_notifications = cursor.fetchall()
            
            # Count unread notifications
            cursor.execute("""
                SELECT COUNT(*) as unread_count
                FROM notifications
                WHERE student_id = ? AND is_read = 0
            """, (user_id,))
            
            unread_count = cursor.fetchone()['unread_count']
            
        else:  # teacher
            # For teachers: Show notifications they've sent (from their courses)
            cursor.execute("""
                SELECT n.*, c.title as course_title, u.full_name as student_name
                FROM notifications n
                LEFT JOIN courses c ON n.course_id = c.id
                LEFT JOIN users u ON n.student_id = u.id
                WHERE c.teacher_id = ?
                ORDER BY n.created_at DESC
            """, (user_id,))
            
            all_notifications = cursor.fetchall()
            
            # Count total notifications sent
            cursor.execute("""
                SELECT COUNT(*) as unread_count
                FROM notifications n
                LEFT JOIN courses c ON n.course_id = c.id
                WHERE c.teacher_id = ?
            """, (user_id,))
            
            unread_count = cursor.fetchone()['unread_count']
        
        conn.close()
        
        return render_template('notifications.html',
                             notifications=all_notifications,
                             unread_count=unread_count,
                             user_role=user_role)
    
    except Exception as e:
        print(f"Error loading notifications: {str(e)}")
        return render_template('error.html', error=f'Error loading notifications: {str(e)}')


# Define route for marking notification as read
@app.route("/mark_notification_read/<int:notification_id>")
def mark_notification_read(notification_id):
    """
    Mark a notification as read.
    
    Args:
        notification_id (int): ID of the notification to mark as read
    
    Returns:
        Redirect back to notifications page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify the notification belongs to the user
        cursor.execute("""
            SELECT id FROM notifications WHERE id = ? AND student_id = ?
        """, (notification_id, session['user_id']))
        
        if not cursor.fetchone():
            conn.close()
            return redirect(url_for('notifications'))
        
        # Mark as read
        cursor.execute("""
            UPDATE notifications SET is_read = 1 WHERE id = ?
        """, (notification_id,))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('notifications'))
    
    except Exception as e:
        return redirect(url_for('notifications'))


# Define route to clear all notifications
@app.route("/clear_all_notifications", methods=['POST'])
def clear_all_notifications():
    """
    Mark all notifications as read for the student.
    
    Returns:
        Redirect back to notifications page
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mark all notifications as read
        cursor.execute("""
            UPDATE notifications SET is_read = 1 WHERE student_id = ? AND is_read = 0
        """, (session['user_id'],))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('notifications'))
    
    except Exception as e:
        return redirect(url_for('notifications'))


# Define route for getting course comments (AJAX)
@app.route("/api/get_comments/<int:course_id>")
def get_comments(course_id):
    """
    Get all comments for a specific course (for AJAX requests).
    
    Args:
        course_id (int): ID of the course
    
    Returns:
        JSON response with list of comments
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_role = session.get('role')
        user_id = session['user_id']
        
        # If course_id is 0, it's a global discussion - all logged-in users can access
        if course_id != 0:
            # Verify user is enrolled in the course (if student) or is the teacher
            if user_role == 'student':
                cursor.execute("""
                    SELECT id FROM enrollments 
                    WHERE student_id = ? AND course_id = ?
                """, (user_id, course_id))
                
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Not enrolled in this course'}), 403
            elif user_role == 'teacher':
                cursor.execute("""
                    SELECT id FROM courses WHERE id = ? AND teacher_id = ?
                """, (course_id, user_id))
                
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Not authorized'}), 403
        
        # Get all comments for the course
        cursor.execute("""
            SELECT c.id, c.message, c.created_at, u.full_name, u.username
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.course_id = ?
            ORDER BY c.created_at DESC
        """, (course_id,))
        
        comments_data = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        comments_list = []
        for comment in comments_data:
            comments_list.append({
                'id': comment['id'],
                'message': comment['message'],
                'created_at': comment['created_at'],
                'full_name': comment['full_name'],
                'username': comment['username']
            })
        
        return jsonify({'success': True, 'comments': comments_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Define route for posting a comment
@app.route("/api/post_comment/<int:course_id>", methods=['POST'])
def post_comment(course_id):
    """
    Post a new comment to a course discussion.
    
    Args:
        course_id (int): ID of the course
    
    Returns:
        JSON response with success status and new comment details
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        message = request.form.get('message', '').strip()
        
        # Validate message
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if len(message) > 5000:
            return jsonify({'error': 'Message is too long (max 5000 characters)'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_id = session['user_id']
        user_role = session.get('role')
        
        # If course_id is 0, it's a global discussion - all logged-in users can post
        if course_id != 0:
            # Verify user is enrolled in the course (if student) or is the teacher
            if user_role == 'student':
                cursor.execute("""
                    SELECT id FROM enrollments 
                    WHERE student_id = ? AND course_id = ?
                """, (user_id, course_id))
                
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Not enrolled in this course'}), 403
            elif user_role == 'teacher':
                cursor.execute("""
                    SELECT id FROM courses WHERE id = ? AND teacher_id = ?
                """, (course_id, user_id))
                
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({'error': 'Not authorized'}), 403
        
        # Insert the new comment
        cursor.execute("""
            INSERT INTO comments (user_id, course_id, message)
            VALUES (?, ?, ?)
        """, (user_id, course_id, message))
        
        conn.commit()
        comment_id = cursor.lastrowid
        
        # Get the comment details with user info
        cursor.execute("""
            SELECT c.id, c.message, c.created_at, u.full_name, u.username
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = ?
        """, (comment_id,))
        
        comment = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'comment': {
                'id': comment['id'],
                'message': comment['message'],
                'created_at': comment['created_at'],
                'full_name': comment['full_name'],
                'username': comment['username']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Define route for deleting a comment
@app.route("/api/delete_comment/<int:comment_id>", methods=['POST'])
def delete_comment(comment_id):
    """
    Delete a comment from a course discussion.
    
    Args:
        comment_id (int): ID of the comment to delete
    
    Returns:
        JSON response with success status
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the comment and verify the user owns it
        cursor.execute("""
            SELECT id, user_id FROM comments WHERE id = ?
        """, (comment_id,))
        
        comment = cursor.fetchone()
        
        if not comment:
            conn.close()
            return jsonify({'error': 'Comment not found'}), 404
        
        # Only the comment author can delete it
        if comment['user_id'] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Not authorized to delete this comment'}), 403
        
        # Delete the comment
        cursor.execute("""
            DELETE FROM comments WHERE id = ?
        """, (comment_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Define error handler for 404 Not Found
@app.errorhandler(404)
def error_404(error):
    """
    Handle 404 Not Found errors.
    
    Returns:
        Rendered error page template with error message
    """
    return render_template('error.html', error='Page not found!'), 404


# Define error handler for 500 Internal Server Error
@app.errorhandler(500)
def error_500(error):
    """
    Handle 500 Internal Server Error.
    
    Returns:
        Rendered error page template with error message
    """
    return render_template('error.html', error='Internal server error!'), 500


# Initialize database tables on application startup
init_db()

# Entry point of the application
if __name__ == "__main__":
    # Run the Flask development server with debug mode enabled
    # debug=True enables auto-reload on code changes and better error messages
    app.run(debug=True)


