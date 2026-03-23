import app.models # Register all models
from app.database import SessionLocal
from app.models import student
from app.services.ml_service import MLService

db = SessionLocal()
students = db.query(student.Student).all()
risks = [MLService.predict_risk(db, s.id).get('risk_status') for s in students]

print("At Risk:", risks.count("At Risk"))
print("Warning:", risks.count("Warning"))
print("Safe:", risks.count("Safe"))
