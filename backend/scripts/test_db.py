import requests

res = requests.get("http://127.0.0.1:8000/students/1/attendance", headers={"Authorization": "Bearer ..."})
# Actually, I don't have a token. Let me just query the db directly.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# add backend dir to path
sys.path.append(r"h:\mini project\vibe\backend")
from app.database import SessionLocal
from app.models.attendance import Attendance
from app.models.subject import Subject
from app.models.student import Student

db = SessionLocal()
attendances = db.query(Attendance).all()
for a in attendances:
    print(f"Att ID: {a.id}, Student: {a.student_id}, Subject ID: {a.subject_id}, Subject Name: {a.subject.name if a.subject else 'None'}")

db.close()
