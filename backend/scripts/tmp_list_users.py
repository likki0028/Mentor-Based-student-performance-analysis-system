from sqlalchemy import text
from app.database import SessionLocal
db = SessionLocal()
rows = db.execute(text("SELECT id, username, email, role FROM users ORDER BY role, id")).fetchall()
for r in rows:
    print(f"ID={r[0]}, user={r[1]}, email={r[2]}, role={r[3]}")
db.close()
