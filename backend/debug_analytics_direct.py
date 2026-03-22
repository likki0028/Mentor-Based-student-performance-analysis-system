
import os
import sys

# Add backend to path
from app.database import SessionLocal, engine
from app.models import user, student, faculty, subject, section, attendance, marks, remark, material, assignment, submission, alert, quiz, quiz_attempt
from app.services.analytics_service import AnalyticsService

# Ensure mapper is initialized
# Base.metadata.create_all(bind=engine) # Not needed if already created

db = SessionLocal()
try:
    student_obj = db.query(student.Student).filter(student.Student.id == 1).first()
    if not student_obj:
        print("Student 1 not found")
        sys.exit(1)
    
    print(f"Testing analytics for: {student_obj.enrollment_number}")
    import time
    start = time.time()
    result = AnalyticsService.get_student_analytics(db, 1)
    end = time.time()
    
    print(f"Time taken: {end - start:.2f}s")
    print(f"Result keys: {result.keys() if result else 'None'}")
    if result:
        print(f"Attendance: {result['attendance_percentage']}%")
        print(f"CGPA: {result['cgpa']}")
        print(f"Subjects in current sem: {len(result['current_semester_details']['subjects'])}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
