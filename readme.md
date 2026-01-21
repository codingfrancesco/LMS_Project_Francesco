# Learning Management System (LMS)

A modern, professional Learning Management System built with Flask and SQLite. This platform enables teachers to create and manage courses, and allows students to enroll, learn, and complete assignments.

## 🎯 Features

### For Students
- ✅ User registration and secure login
- ✅ Browse and enroll in available courses
- ✅ View course lessons and topics
- ✅ Complete assignments and quizzes
- ✅ Track learning progress
- ✅ View submission history
- ✅ Personal dashboard with statistics

### For Teachers
- ✅ User registration and secure login
- ✅ Create and manage courses
- ✅ Add lessons and topics to courses
- ✅ Create multiple-choice questions
- ✅ View enrolled students
- ✅ Track student progress
- ✅ Teacher dashboard with analytics

### General Features
- ✅ Modern, responsive UI with blue/navy color scheme
- ✅ Secure password hashing (SHA256)
- ✅ Session management for user authentication
- ✅ Role-based access control (Student/Teacher)
- ✅ Database-driven content management
- ✅ Professional styling with CSS variables
- ✅ Mobile-friendly design

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Database**: SQLite 3
- **Authentication**: Session-based with password hashing
- **Language**: Python 3

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS variables and flexbox
- **JavaScript**: Interactive features and form validation
- **Bootstrap-like**: Custom responsive grid system

## 📁 Project Structure

```
LMS_Project_Francesco/
├── app.py                          # Main Flask application
├── lms.db                          # SQLite database
├── readme.md                       # This file
├── static/
│   ├── style.css                   # Global stylesheet
│   └── css/
│       └── style/
└── templates/
    ├── base.html                   # Base template (navbar, footer)
    ├── home.html                   # Homepage
    ├── login.html                  # Login page
    ├── register.html               # Registration page
    ├── student_dashboard.html      # Student dashboard
    ├── teacher_dashboard.html      # Teacher dashboard
    ├── course.html                 # Courses listing page
    ├── lessons.html                # Lessons/topics page
    ├── assignments.html            # Assignments/quizzes page
    └── other pages...
```

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- Flask
- SQLite3 (included with Python)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/codingfrancesco/LMS_Project_Francesco.git
   cd LMS_Project_Francesco
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   Navigate to `http://localhost:5000`

## 📊 Database Schema

### users
- `id` - User ID (Primary Key)
- `username` - Unique username
- `email` - Unique email address
- `password` - Hashed password (SHA256)
- `full_name` - User's full name
- `role` - User role: 'student' or 'teacher'
- `created_at` - Account creation timestamp
- `last_login` - Last login timestamp

### courses
- `id` - Course ID (Primary Key)
- `course_id` - Unique course number
- `title` - Course title
- `description` - Course description
- `teacher_id` - Teacher who created course (Foreign Key)
- `created_at` - Creation timestamp

### topics
- `id` - Topic ID (Primary Key)
- `course_id` - Associated course (Foreign Key)
- `title` - Topic title
- `subtitle` - Topic subtitle/description
- `created_at` - Creation timestamp

### msqs (Multiple Choice Questions)
- `id` - Question ID (Primary Key)
- `topic_id` - Associated topic (Foreign Key)
- `question` - Question text
- `option_a` - Option A text
- `option_b` - Option B text
- `option_c` - Option C text
- `option_d` - Option D text
- `correct_answer` - Correct answer: 'a', 'b', 'c', or 'd'
- `created_at` - Creation timestamp

### enrollments
- `id` - Enrollment ID (Primary Key)
- `student_id` - Student ID (Foreign Key)
- `course_id` - Course ID (Foreign Key)
- `enrolled_at` - Enrollment timestamp
- `progress` - Progress percentage (0-100)

### submissions
- `id` - Submission ID (Primary Key)
- `student_id` - Student ID (Foreign Key)
- `question_id` - Question ID (Foreign Key)
- `selected_answer` - Student's answer: 'a', 'b', 'c', or 'd'
- `is_correct` - Whether answer is correct (1 or 0)
- `submitted_at` - Submission timestamp

## 🔐 Security Features

- **Password Hashing**: SHA256 encryption for all passwords
- **Session Management**: Secure user sessions with Flask sessions
- **Input Validation**: Server-side validation of all inputs
- **SQL Injection Prevention**: Parameterized queries (?)
- **CSRF Protection**: Form validation on server
- **Role-Based Access**: Different pages for students and teachers

## 🎨 Design & Styling

### Color Scheme
- **Primary Navy**: #1a2f5a (Dark blue headings)
- **Primary Blue**: #2d5a96 (Navigation, primary elements)
- **Accent Blue**: #4a90e2 (Links, buttons, highlights)
- **Light Blue**: #e8f0f8 (Light backgrounds)
- **Text Colors**: Dark blue, medium gray, light gray

### Typography
- **Font Stack**: System fonts (-apple-system, Segoe UI, Roboto)
- **Heading Sizes**: H1 (36px), H2 (28px), H3 (22px), H4 (18px)
- **Body Text**: 16px with 1.6 line height
- **Font Weight**: 600 (bold), 700 (extra bold), 500 (medium)

### Responsive Design
- Mobile: 320px+
- Tablet: 768px+
- Desktop: 1024px+
- Wide: 1440px+

## 📝 User Workflows

### Student Registration & Login
1. Click "Register" on navigation bar
2. Fill in registration form (name, username, email, password)
3. Select "Student" as account type
4. Click "Create Account"
5. Redirected to login page
6. Enter credentials and click "Sign In"
7. Redirected to Student Dashboard

### Student Actions
1. **View Courses**: Click "Courses" or "Browse All Courses"
2. **Enroll in Course**: Click "Enroll Now" on any course
3. **View Lessons**: Click "Lessons" or "Continue Learning"
4. **Complete Assignments**: Click "Assignments" and submit answers
5. **Track Progress**: View progress bar on dashboard

### Teacher Registration & Login
1. Click "Register" on navigation bar
2. Fill in registration form
3. Select "Teacher" as account type
4. Click "Create Account"
5. Login with credentials
6. Redirected to Teacher Dashboard

### Teacher Actions
1. **Create Course**: Click "+ Create New Course"
2. **Add Topics**: Click "Manage" on course
3. **Create Questions**: Add MCQ questions to topics
4. **View Students**: See enrolled students on dashboard
5. **Track Progress**: View student submissions

## 🔄 API Routes

### Authentication
- `GET /` - Homepage
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /register` - Registration page
- `POST /register` - Process registration
- `GET /logout` - Logout user

### Student Routes
- `GET /student_dashboard` - Student dashboard
- `GET /course` - Browse all courses
- `GET /lessons` - Browse all lessons
- `GET /assignments` - View assignments

### Teacher Routes
- `GET /teacher_dashboard` - Teacher dashboard

## 💾 Database Initialization

The database is automatically created on first run. The `init_db()` function:
- Creates all tables if they don't exist
- Sets up foreign key relationships
- Adds unique constraints where needed
- Runs on application startup

## 🐛 Troubleshooting

### "no such table" Error
**Solution**: Delete `lms.db` and restart the application. The database will be recreated automatically.

### Login Fails
- Ensure username/password are correct
- Check if user exists in database
- Verify password is at least 6 characters

### Session Issues
- Clear browser cookies
- Restart Flask application
- Check if `SECRET_KEY` is set properly

## 🚦 Development Tips

### Adding New Pages
1. Create HTML template in `templates/` folder
2. Extend `base.html` with `{% extends 'base.html' %}`
3. Add route in `app.py`
4. Link in navigation menu in `base.html`

### Styling Elements
- Use CSS classes from `style.css`
- Use CSS variables: `var(--primary-navy)`, `var(--accent-blue)`, etc.
- Use utility classes: `mt-30`, `mb-20`, `text-center`, etc.

### Adding Database Columns
1. Modify the CREATE TABLE statement in `init_db()`
2. Delete `lms.db` to recreate with new schema
3. Restart application

## 📈 Future Enhancements

- [ ] Password reset functionality
- [ ] Course certificates upon completion
- [ ] Discussion forum for students
- [ ] File upload for assignments
- [ ] Gradebook and GPA calculation
- [ ] Email notifications
- [ ] Student groups and teams
- [ ] Advanced search and filtering
- [ ] Admin panel for system management
- [ ] Analytics and reporting dashboard
- [ ] Mobile app
- [ ] OAuth2 integration (Google, GitHub)

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Francesco**
- GitHub: [@codingfrancesco](https://github.com/codingfrancesco)
- Project: LMS_Project_Francesco

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Last Updated**: January 21, 2026
**Version**: 1.0.0
**Status**: Active Development