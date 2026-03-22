from app.database import engine, SessionLocal
from app.models import subject as subject_model
from app.main import app

db = SessionLocal()
try:
    subjects = db.query(subject_model.Subject).all()
    for s in subjects:
        print(s.name, s.subject_type)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
