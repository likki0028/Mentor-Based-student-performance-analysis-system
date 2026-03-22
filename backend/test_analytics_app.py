from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.services.analytics_service import AnalyticsService

db = SessionLocal()
try:
    # 1. Manually test analytics service for student ID=1
    # We bypass login to directly verify the logic.
    student_id = 1
    print("Fetching analytics from service for Student ID 1...")
    data = AnalyticsService.get_student_analytics(db, student_id)
    
    if not data:
        print("No data found for student 1")
    else:
        print(f"\n--- Analytics for {data['name']} ({data['enrollment_number']}) ---")
        print(f"Current Semester: {data['current_semester']}")
        print(f"CGPA (Sem 1-5 only): {data['cgpa']}")
        print(f"Overall Attendance: {data['attendance_percentage']}%")

        print("\n--- COMPLETED SEMESTERS (1-5) ---")
        for sem in data.get('semester_stats', []):
            print(f"\nSemester {sem['semester']} - SGPA: {sem['sgpa']} - Attendance: {sem['attendance_percentage']}%")
            for sub in sem['subject_stats'][:3]: # print first 3
                print(f"  [{sub.get('subject_type')}] {sub['subject_name']}: {sub.get('grade_point')} GP, {sub['attendance_percentage']}% att")

        print("\n--- CURRENT SEMESTER (6) ---")
        curr = data.get('current_semester_details', {})
        print(f"Semester {curr.get('semester', 'N/A')}")
        for sub in curr.get('subjects', []):
            print(f"\n  [{sub.get('subject_type')}] {sub['subject_name']}")
            print(f"    Sessional Marks: {sub.get('sessional_marks')}")
            print(f"    Attendance: {sub['attendance_percentage']}%")
            if sub.get('assignment_count', 0) > 0:
                print(f"    Assignments ({sub['assignments_submitted']}/{sub['assignment_count']} submitted):")
                for a in sub['assignment_details']:
                    print(f"      - {a['title']}: {a['status']} (Due: {a['due_date']})")

finally:
    db.close()
