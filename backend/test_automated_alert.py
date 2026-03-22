
import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime

# Add the parent directory of 'backend' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.database import SessionLocal
from app.models import marks as marks_model
from app.models import subject as subject_model
from app.services.alert_service import AlertService

def trigger_test_alert():
    db = SessionLocal()
    try:
        student_id = 21 # sectionb_stu_1
        subject_id = 1 # Just pick one
        
        print(f"Adding low marks for student {student_id} to trigger alert...")
        
        # Add 3 low marks to ensure average is < 40
        for i in range(3):
            mark = marks_model.Marks(
                student_id=student_id,
                subject_id=subject_id,
                assessment_type=marks_model.AssessmentType.INTERNAL,
                score=10,
                total=100
            )
            db.add(mark)
        
        db.commit()
        print("Marks added successfully. Triggering alerts...")
        
        # This is now also automatically triggered in marks_router.py, 
        # but I'll call it here manually to see the output.
        alerts_created = AlertService.generate_alerts(db)
        print(f"Alerts generated: {alerts_created}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    trigger_test_alert()
