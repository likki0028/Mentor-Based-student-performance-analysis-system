import requests
import json
import sys

# Replace with the actual student ID in the DB, e.g., 61 (which might be the student from the screenshot)
# The username in screenshot is 23241a6701. Let's find that student.

import os
sys.path.append(r"h:\mini project\vibe\backend")
from app.database import SessionLocal
from app.models.student import Student
from app.models.user import User
from app.models.attendance import Attendance

db = SessionLocal()
u = db.query(User).filter(User.username == "23241a6701").first()
if getattr(u, 'id', None):
    s = db.query(Student).filter(Student.user_id == u.id).first()
    print(f"Student ID: {s.id}")
    atts = db.query(Attendance).filter(Attendance.student_id == s.id).all()
    for a in atts:
        print(f"Att_id: {a.id}, Date: {a.date}, Period: {a.period}, Status: {a.status}, Subj_id: {a.subject_id}, Subj_name: {a.subject.name if a.subject else 'None'}")
db.close()
