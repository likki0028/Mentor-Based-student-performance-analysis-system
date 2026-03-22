"""
Debug the 500 error on /analytics/student endpoint
Run from backend dir: python debug_student196.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import ALL models first so SQLAlchemy mapper can resolve all relationships
from app.models import (
    user, student, faculty, subject, section,
    remark, material, marks, attendance, assignment,
    submission, alert, quiz, quiz_attempt
)

from app.database import SessionLocal
from app.services.analytics_service import AnalyticsService

db = SessionLocal()
try:
    for student_id in [1, 196]:
        print(f"\n=== Testing student {student_id} ===")
        try:
            result = AnalyticsService.get_student_analytics(db, student_id)
            if result:
                subs = result.get("current_semester_details", {}).get("subjects", [])
                print(f"  OK - {len(subs)} subjects in current semester")
                for s in subs:
                    print(f"    {s['subject_name']}: {s['sessional_marks']}")
            else:
                print(f"  NOT FOUND (None returned)")
        except Exception as e:
            import traceback
            print(f"  ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()
finally:
    db.close()
