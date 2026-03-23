"""
Apply perfectly generated JSON data to the active local database
without dropping any tables or touching faculty/admin users.
Only updates Section B students, their marks, and attendance.
"""

import json
import os
import random
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime
import psycopg2 # Ensures psycopg2 is loaded if using neon

# Force local SQLite DB for this run overriding .env
os.environ["DATABASE_URL"] = "sqlite:///./sql_app.db"

import app.models # Trigger registrations
from app.models import user, student, section, subject, marks, attendance, faculty
from app.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker

# 100% force local sqlite
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from scripts.generate_synthetic_data import CURRICULUM

def apply_data():
    db = SessionLocal()
    
    # Load JSON
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "scripts", "synthetic_students.json")
    if not os.path.exists(json_path):
        json_path = os.path.join(script_dir, "synthetic_students.json")
        
    with open(json_path, "r", encoding="utf-8") as f:
        synthetic_students = json.load(f)
        
    print(f"Loaded {len(synthetic_students)} perfectly generated students from JSON.")
    
    # Grab Section B ID
    sec_b = db.query(section.Section).filter(section.Section.name == "Section B").first()
    if not sec_b:
        print("Section B not found in DB! Creating...")
        sec_b = section.Section(name="Section B")
        db.add(sec_b)
        db.commit()
        db.refresh(sec_b)
        
    # Get all faculty to assign mentors randomly if needed
    all_facs = db.query(faculty.Faculty).all()
    default_mentor_id = all_facs[0].id if all_facs else None

    # We need subject codes mapped to DB subject IDs
    db_subjects = {s.code: s.id for s in db.query(subject.Subject).all()}
    if not db_subjects:
        print("ERROR: Subjects not found in database! Make sure basic seeding was done.")
        return
        
    student_ids_processed = []
    marks_created = 0
    att_created = 0
    
    for s_data in synthetic_students:
        s_uname = s_data["student_id"].lower()
        
        # 1. Upsert User
        db_user = db.query(user.User).filter(user.User.username == s_uname).first()
        if not db_user:
            db_user = user.User(
                username=s_uname,
                email=f"{s_uname}@griet.ac.in",
                hashed_password=get_password_hash("student123"),
                role=user.UserRole.STUDENT,
                is_active=True
            )
            db.add(db_user)
            db.flush()
            
        # 2. Upsert Student
        db_student = db.query(student.Student).filter(student.Student.user_id == db_user.id).first()
        if not db_student:
            db_student = student.Student(
                user_id=db_user.id,
                enrollment_number=s_data["student_id"],
                current_semester=6, # Based on demo showing till smt 5
                section_id=sec_b.id,
                mentor_id=default_mentor_id
            )
            db.add(db_student)
            db.flush()
            
        student_ids_processed.append(db_student.id)
        
        # 3. Clear existing marks and attendance for this student to ensure a clean slate
        db.query(marks.Marks).filter(marks.Marks.student_id == db_student.id).delete()
        db.query(attendance.Attendance).filter(attendance.Attendance.student_id == db_student.id).delete()
        
        # Track Backlogs on the student model!
        db_student.backlogs = s_data["backlogs"]
        db.add(db_student)
        
        # 4. Insert New Marks
        for sem_data in s_data["semesters"]:
            sem_num = sem_data["semester"]
            for subj_idx, subj_data in enumerate(sem_data["subjects"]):
                code = subj_data["code"]
                db_sub_id = db_subjects.get(code)
                if not db_sub_id:
                    continue # Skip if subject missing
                    
                m = subj_data["marks"]
                
                # Check models/marks.py for AssessmentType enum
                from app.models.marks import AssessmentType, Marks
                
                if subj_data["type"] == "Theory":
                    # Mid 1
                    db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.MID_TERM, score=m["mid1_total"], total=30))
                    # Mid 2
                    db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.MID_TERM, score=m["mid2_total"], total=30))
                    # Internal
                    db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.INTERNAL, score=m["internal_total"], total=40))
                    if sem_num < 6:
                        # External
                        db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.END_TERM, score=m["external"], total=60))
                        marks_created += 1
                    marks_created += 3
                    
                elif subj_data["type"] == "Lab":
                    db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.INTERNAL, score=m["internal_total"], total=40))
                    if sem_num < 6:
                        db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.END_TERM, score=m["external"], total=60))
                        marks_created += 1
                    marks_created += 1
                    
                else: # Non-Credit
                    db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.MID_TERM, score=m["mid1"], total=40))
                    db.add(Marks(student_id=db_student.id, subject_id=db_sub_id, assessment_type=AssessmentType.MID_TERM, score=m["mid2"], total=40))
                    marks_created += 2
                
        # 5. Insert New Attendance
        # We simulate ~15 attendance records per subject across the latest semester for dashboard
        att_rate = s_data["overall_attendance_rate"]
        latest_sem = s_data["semesters"][-1]
        for subj_data in latest_sem["subjects"]:
            code = subj_data["code"]
            db_sub_id = db_subjects.get(code)
            if not db_sub_id: continue
            
            for d in range(15):
                status = True if random.random() < att_rate else False
                db.add(attendance.Attendance(
                    student_id=db_student.id,
                    subject_id=db_sub_id,
                    date=datetime.utcnow().date(), # All today for demo simplicity
                    status=status
                ))
                att_created += 1
                
        if len(student_ids_processed) % 10 == 0:
            db.commit()
            print(f"Processed {len(student_ids_processed)} students...")

    db.commit()
    print(f"\nSUCCESS! Updated {len(student_ids_processed)} Section B students.")
    print(f"Created {marks_created} Marks records and {att_created} Attendance records.")
    
if __name__ == "__main__":
    apply_data()
