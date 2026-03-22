import os
import json
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.main import app  # ensure all models are imported
from app.services.analytics_service import AnalyticsService

# Create a session
db = SessionLocal()

try:
    student_id = 196
    print("Fetching analytics from service for student 196...")
    data = AnalyticsService.get_student_analytics(db, student_id)
    
    if not data:
        print("No data found for student 196")
    else:
        print("Success! Data loaded:")
        print(f"CGPA: {data['cgpa']}")
        print(f"Current Semester: {data['current_semester']}")
        print(f"Overall Attendance: {data['attendance_percentage']}%")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
