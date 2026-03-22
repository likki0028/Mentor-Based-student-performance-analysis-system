from app.models.marks import AssessmentType, Marks
from app.database import SessionLocal

print("Enum Mapping:")
for name, member in AssessmentType.__members__.items():
    print(f"  {name} -> {member.value}")

db = SessionLocal()
try:
    m = db.query(Marks).filter(Marks.id == 107).first()
    if m:
        print(f"\nRow ID 107:")
        print(f"  assessment_type (attr): {m.assessment_type}")
        print(f"  type: {type(m.assessment_type)}")
        if hasattr(m.assessment_type, 'value'):
            print(f"  value: {m.assessment_type.value}")
        
        # Check raw database value via SQLAlchemy text query
        from sqlalchemy import text
        raw = db.execute(text("SELECT assessment_type FROM marks WHERE id=107")).fetchone()
        print(f"  Raw DB value: {raw[0]}")
    else:
        print("\nRow ID 107 not found.")
finally:
    db.close()
