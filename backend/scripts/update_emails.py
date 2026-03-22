import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Update emails for test users
db.execute(text("UPDATE users SET email='likhithbalaji90@gmail.com' WHERE username='niharika'"))
db.execute(text("UPDATE users SET email='hyperbeast2006m@gmail.com' WHERE username='sasibhanu'"))
db.execute(text("UPDATE users SET email='likhithbalaji2006m@gmail.com' WHERE username='23241a6701'"))
db.commit()

# Verify
rows = db.execute(text("SELECT username, email, role FROM users WHERE email IS NOT NULL AND email != '' ORDER BY role")).fetchall()
for r in rows:
    print(f"{r[0]}: {r[1]} ({r[2]})")

db.close()
print("\nDone!")
