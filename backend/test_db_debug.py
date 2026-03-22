import sys, os
sys.path.insert(0, os.getcwd())
from app.database import SessionLocal
from app.models.marks import Marks
from app.models.subject import Subject

db = SessionLocal()
try:
    print("CHECKING ALL MARKS")
    marks_recs = db.query(Marks).all()
    for m in marks_recs:
        sub = db.query(Subject).filter(Subject.id == m.subject_id).first()
        print(f"Mark ID {m.id}: Subject ID {m.subject_id}, Subject Name {sub.name if sub else 'NOT FOUND'}")
finally:
    db.close()
