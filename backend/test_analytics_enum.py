from app.database import SessionLocal
from app.models.marks import Marks
from app.models.subject import Subject
from app.services.analytics_service import AnalyticsService

db = SessionLocal()
try:
    print("Direct marks query for student 1, sem 6:")
    marks = db.query(Marks).join(Subject).filter(Subject.semester==6, Marks.student_id==1).all()
    for m in marks:
        val = m.assessment_type.value if hasattr(m.assessment_type, 'value') else str(m.assessment_type)
        print(f"Sub {m.subject_id}: {val} => {m.score}/{m.total} | RAW: type({type(m.assessment_type)}) repr({repr(m.assessment_type)})")
        
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
