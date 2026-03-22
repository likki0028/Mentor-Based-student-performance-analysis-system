"""
Lightweight Seed Data Script
=============================
Creates a minimal dataset for UI testing.
- 1 Admin
- 1 Mentor (mentor_a)
- 1 Lecturer
- 3 Students
- 1 Subject, 1 Section
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend dir to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    user, student, faculty, subject, section,
    attendance, marks, alert, assignment, submission, remark, material
)
from app.core.security import get_password_hash

def seed_lite():
    db = SessionLocal()
    try:
        print("=" * 40)
        print("SEED LITE — Minimal Demo Dataset")
        print("=" * 40)

        # Create tables
        Base.metadata.create_all(bind=engine)

        # 1. Clear existing data
        print("Clearing database...")
        for table in [remark.Remark, alert.Alert, submission.Submission, 
                      assignment.Assignment, material.Material, marks.Marks, 
                      attendance.Attendance, student.Student, faculty.Faculty, 
                      section.Section, subject.Subject, user.User]:
            db.query(table).delete()
        db.commit()

        # 2. Users & Roles
        print("Creating users...")
        
        # Admin
        admin = user.User(username="admin", hashed_password=get_password_hash("admin123"), role=user.UserRole.ADMIN)
        
        # Mentor A
        mentor_a = user.User(username="mentor_a", hashed_password=get_password_hash("mentor123"), role=user.UserRole.MENTOR)
        
        # Lecturer
        lect = user.User(username="lecturer", hashed_password=get_password_hash("lecturer123"), role=user.UserRole.LECTURER)
        
        db.add_all([admin, mentor_a, lect])
        db.commit()

        # Faculty Profiles
        fac_mentor = faculty.Faculty(user_id=mentor_a.id, employee_id="FAC001")
        fac_lect = faculty.Faculty(user_id=lect.id, employee_id="FAC002")
        db.add_all([fac_mentor, fac_lect])
        db.commit()

        # 3. Section & Subject
        print("Creating academics...")
        sec_a = section.Section(name="Section A")
        sub_ml = subject.Subject(name="Machine Learning", code="CS101", semester=6, subject_type=subject.SubjectType.THEORY, credits=3)
        db.add_all([sec_a, sub_ml])
        
        # Historical Subjects (for GPA chart)
        hist_subs = []
        for sem in range(1, 6):
            s = subject.Subject(name=f"Past Subject {sem}", code=f"HIS0{sem}", semester=sem, subject_type=subject.SubjectType.THEORY, credits=3)
            db.add(s)
            hist_subs.append(s)
        
        db.commit()

        # Material & Assignment (for Lecturer dashboard to work)
        db.add(material.Material(title="ML Syllabus", file_url="/dummy.pdf", subject_id=sub_ml.id, section_id=sec_a.id, faculty_id=fac_mentor.id))
        db.add(assignment.Assignment(title="Intro Assignment", due_date=datetime.utcnow() + timedelta(days=7), subject_id=sub_ml.id, section_id=sec_a.id, faculty_id=fac_mentor.id))
        db.commit()

        # 4. Students
        print("Creating students...")
        stu_users = []
        for i in range(1, 4):
            u = user.User(username=f"student{i}", hashed_password=get_password_hash("student123"), role=user.UserRole.STUDENT)
            db.add(u)
            stu_users.append(u)
        db.commit()

        # Add the explicit 'student' user for the login button
        base_student = user.User(username="student", hashed_password=get_password_hash("student123"), role=user.UserRole.STUDENT)
        db.add(base_student)
        db.commit()

        students = []
        for i, u in enumerate(stu_users + [base_student]):
            s = student.Student(user_id=u.id, enrollment_number=f"ENR100{i}", current_semester=6, mentor_id=fac_mentor.id, section_id=sec_a.id)
            db.add(s)
            students.append(s)
        db.commit()

        # 5. Marks & Attendance
        print("Creating marks and attendance...")
        for student_obj in students:
            # Current Sem
            db.add(marks.Marks(student_id=student_obj.id, subject_id=sub_ml.id, assessment_type=marks.AssessmentType.MID_TERM, score=25, total=30))
            db.add(attendance.Attendance(student_id=student_obj.id, subject_id=sub_ml.id, date=datetime.utcnow().date(), status=True))
            
            # Historical Marks (varying GPA)
            for i, hs in enumerate(hist_subs):
                # Varying scores to show a trend: 70%, 75%, 85%, 80%, 90%
                base_scores = [21, 23, 26, 24, 28] 
                score = base_scores[i]
                db.add(marks.Marks(student_id=student_obj.id, subject_id=hs.id, assessment_type=marks.AssessmentType.END_TERM, score=score, total=30))
                # High attendance for history
                db.add(attendance.Attendance(student_id=student_obj.id, subject_id=hs.id, date=datetime.utcnow().date() - timedelta(days=200-i*30), status=True))
        
        db.commit()

        print("Done! Database is now seeded with lite dataset.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_lite()
