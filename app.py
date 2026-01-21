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
            -- ID of the teacher who created this course
            teacher_id INTEGER,
            -- Timestamp when course was created
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign key linking to the teacher user
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        )
    """)
    
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
            -- Timestamp when topic was created
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Foreign key linking to courses table
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
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
    
    # Render home.html template and pass the statistics as variables
    # These variables can be used in the HTML template with {{ variable_name }}
    return render_template('home.html', 
                         courses_count=courses_count,
                         topics_count=topics_count,
                         users_count=users_count)


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
        
        # Close connection
        conn.close()
        
        # Render teacher dashboard template with statistics
        return render_template('teacher_dashboard.html',
                             my_courses=my_courses,
                             total_students=total_students,
                             total_assignments=total_assignments,
                             full_name=session.get('full_name'))
    
    except Exception as e:
        # Handle any database errors
        return render_template('teacher_dashboard.html', my_courses=[], error='Error loading courses')


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


# Define route for courses page
@app.route("/course")
def course():
    """
    Render the courses page with all available courses.
    
    Fetches all courses from the database.
    
    Returns:
        Rendered HTML template with courses data
    """
    try:
        # Try to fetch courses from database
        # Establish connection to the database
        conn = get_db_connection()
        # Create cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Execute SQL query to fetch all courses
        # SELECT id, title, description, course_id: Get course details
        # FROM courses: Select from courses table
        # ORDER BY id DESC: Sort by course ID in descending order (newest first)
        cursor.execute("""
            SELECT id, title, description, course_id 
            FROM courses 
            ORDER BY id DESC
        """)
        # Fetch all results from the query and store in courses_data list
        courses_data = cursor.fetchall()
        # Close the database connection to free resources
        conn.close()
    except sqlite3.OperationalError:
        # If courses table doesn't exist, return empty list
        courses_data = []
    
    # Render course.html template and pass courses data as variable
    # The template can loop through this data with {% for course in courses %}
    return render_template('course.html', courses=courses_data)


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


# Initialize database tables on application startup
init_db()

# Entry point of the application
if __name__ == "__main__":
    # Run the Flask development server with debug mode enabled
    # debug=True enables auto-reload on code changes and better error messages
    app.run(debug=True)


