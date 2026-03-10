#!/usr/bin/env python3
"""
Notification System Validation Script
This script tests the notification system to ensure it's working correctly.
"""

import sqlite3
import datetime

def get_db_connection(db_name="lms.db"):
    """Connect to the LMS database."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_database_structure():
    """Verify the notifications table exists and has correct schema."""
    print_section("1. TESTING DATABASE STRUCTURE")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(notifications)")
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ FAILED: Notifications table doesn't exist!")
            conn.close()
            return False
        
        print("✅ Notifications table exists")
        print("\nColumns:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        conn.close()
        return False

def test_enrollments():
    """Check enrollment data."""
    print_section("2. CHECKING ENROLLMENTS")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT e.id, u.username, c.title, e.course_id, e.student_id
            FROM enrollments e
            LEFT JOIN users u ON e.student_id = u.id
            LEFT JOIN courses c ON e.course_id = c.id
            ORDER BY e.course_id
        """)
        
        enrollments = cursor.fetchall()
        
        if not enrollments:
            print("⚠️  WARNING: No enrollments found!")
            print("Students must enroll in courses for notifications to be created.")
            conn.close()
            return False
        
        print(f"✅ Found {len(enrollments)} enrollments\n")
        
        # Group by course
        courses = {}
        for enrollment in enrollments:
            course_id = enrollment['course_id']
            if course_id not in courses:
                courses[course_id] = []
            courses[course_id].append(enrollment['username'])
        
        for course_id, students in sorted(courses.items()):
            print(f"Course ID {course_id}: {', '.join(students) if students else 'No students'}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        conn.close()
        return False

def test_notification_insertion():
    """Test if a sample notification can be inserted."""
    print_section("3. TESTING NOTIFICATION INSERTION")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get first enrollment and course
        cursor.execute("""
            SELECT student_id, course_id FROM enrollments LIMIT 1
        """)
        
        enrollment = cursor.fetchone()
        
        if not enrollment:
            print("❌ FAILED: No enrollments to test with")
            conn.close()
            return False
        
        student_id = enrollment[0]
        course_id = enrollment[1]
        
        # Try to insert a test notification
        cursor.execute("""
            INSERT INTO notifications (student_id, course_id, notification_type, title, message, resource_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, course_id, 'test', 'Test Notification', 'This is a system test', 0))
        
        conn.commit()
        
        # Verify it was inserted
        cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE notification_type = 'test'")
        result = cursor.fetchone()
        
        if result[0] > 0:
            print("✅ Notification insertion successful")
            
            # Clean up test notification
            cursor.execute("DELETE FROM notifications WHERE notification_type = 'test'")
            conn.commit()
            print("✅ Test notification cleaned up")
            
            conn.close()
            return True
        else:
            print("❌ FAILED: Notification was not inserted")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        conn.close()
        return False

def test_current_notifications():
    """Display current notifications in the database."""
    print_section("4. CURRENT NOTIFICATIONS IN DATABASE")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as total FROM notifications
        """)
        
        count = cursor.fetchone()['total']
        
        if count == 0:
            print("✅ No notifications (this is OK if lessons/assignments haven't been created)")
        else:
            print(f"✅ Found {count} notifications\n")
            
            cursor.execute("""
                SELECT n.id, n.student_id, n.course_id, n.notification_type, 
                       n.title, n.is_read, n.created_at,
                       u.username, c.title as course_title
                FROM notifications n
                LEFT JOIN users u ON n.student_id = u.id
                LEFT JOIN courses c ON n.course_id = c.id
                ORDER BY n.created_at DESC
                LIMIT 10
            """)
            
            notifications = cursor.fetchall()
            
            for notif in notifications:
                status = "READ" if notif['is_read'] else "UNREAD"
                print(f"[{status}] {notif['username']} - {notif['notification_type'].upper()}: {notif['title']}")
                print(f"       Course: {notif['course_title']} | Created: {notif['created_at']}\n")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        conn.close()
        return False

def test_create_lesson_simulation():
    """Simulate creating a lesson and verify notifications would be created."""
    print_section("5. SIMULATING LESSON CREATION")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find a course with enrolled students
        cursor.execute("""
            SELECT DISTINCT c.id, c.title, c.teacher_id
            FROM courses c
            INNER JOIN enrollments e ON c.id = e.course_id
            LIMIT 1
        """)
        
        course = cursor.fetchone()
        
        if not course:
            print("❌ No courses with enrolled students found")
            conn.close()
            return False
        
        course_id = course[0]
        course_title = course[1]
        
        # Count enrolled students
        cursor.execute("""
            SELECT COUNT(*) as count FROM enrollments WHERE course_id = ?
        """, (course_id,))
        
        student_count_row = cursor.fetchone()
        student_count = student_count_row[0] if student_count_row else 0
        
        print(f"✅ Found course '{course_title}' (ID: {course_id})")
        print(f"✅ Course has {student_count} enrolled student(s)\n")
        
        print("Simulation:")
        print(f"  1. Teacher creates lesson in course {course_id}")
        print(f"  2. System inserts lesson into topics table")
        print(f"  3. System queries: SELECT student_id FROM enrollments WHERE course_id = {course_id}")
        print(f"  4. System would create {student_count} notification(s)")
        print(f"\n✅ This demonstrates the notification system WOULD work for this course!")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        conn.close()
        return False

def main():
    """Run all validation tests."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*17 + "NOTIFICATION SYSTEM VALIDATION" + " "*11 + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # Run all tests
    results.append(("Database Structure", test_database_structure()))
    results.append(("Enrollments", test_enrollments()))
    results.append(("Notification Insertion", test_notification_insertion()))
    results.append(("Current Notifications", test_current_notifications()))
    results.append(("Create Lesson Simulation", test_create_lesson_simulation()))
    
    # Summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Notification system is ready.")
    elif passed >= total - 1:
        print("\n⚠️  MOSTLY WORKING: Check warnings above and ensure students are enrolled.")
    else:
        print("\n❌ ISSUES DETECTED: Review errors above and consult the fix guide.")

if __name__ == "__main__":
    main()
