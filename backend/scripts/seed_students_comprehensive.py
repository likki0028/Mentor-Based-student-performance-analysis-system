import sys
import os
import random

# Add backend dir to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import user, student, faculty, section, subject, marks, attendance
from app.core.security import get_password_hash
from datetime import datetime, timedelta

def seed_students():
    db = SessionLocal()
    try:
        print("GENERATING COMPREHENSIVE STUDENT DATASET...")
        
        # 1. Clear existing students/marks/attendance to avoid confusion
        print("Clearing existing student data...")
        db.query(attendance.Attendance).delete()
        db.query(marks.Marks).delete()
        db.query(student.Student).delete()
        # Keep the 'student' and 'student1-3' users but we'll link them or create new ones
        db.commit()

        # 2. Get Mentors (Faculty IDs)
        # Section A: Ms. Rashi Saxena (1770)
        # Section B: Ms. D. S. Niharika (1838)
        # Section C: Ms. S. Srilatha (1837)
        
        mentors_map = {}
        for sec_name, emp_id in [("Section A", "1770"), ("Section B", "1838"), ("Section C", "1837")]:
            fac = db.query(faculty.Faculty).filter(faculty.Faculty.employee_id == emp_id).first()
            sec = db.query(section.Section).filter(section.Section.name == sec_name).first()
            if fac and sec:
                mentors_map[sec.id] = fac.id

        # 3. Generate 20 students per section
        first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Karthik", "Ishani", "Arjun", "Aditi", 
                       "Sanjay", "Kavya", "Manish", "Riya", "Nikhil", "Pooja", "Varun", "Meera", "Rohan", "Sonal"]
        last_names = ["Sharma", "Verma", "Gupta", "Malhotra", "Iyer", "Reddy", "Patel", "Singh", "Nair", "Joshi"]

        sections = db.query(section.Section).filter(section.Section.name.in_(["Section A", "Section B", "Section C"])).all()
        
        # We need some subjects for marks/attendance
        subs = db.query(subject.Subject).filter(subject.Subject.semester == 6).all()

        for sec in sections:
            mentor_id = mentors_map.get(sec.id)
            print(f"Generating 20 students for {sec.name}...")
            
            for i in range(1, 21):
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                uname = f"{sec.name.replace(' ', '').lower()}_stu_{i}"
                enroll = f"22241A-{sec.name[-1]}-{i:02d}"
                
                # User
                u = user.User(username=uname, hashed_password=get_password_hash("student123"), role=user.UserRole.STUDENT)
                db.add(u)
                db.flush()
                
                # Student Profile
                s = student.Student(
                    user_id=u.id, 
                    enrollment_number=enroll, 
                    current_semester=6, 
                    section_id=sec.id, 
                    mentor_id=mentor_id
                )
                db.add(s)
                db.flush()

                # Add some initial attendance and marks for these students
                if subs:
                    for sub in subs:
                        # Random attendance 75-95%
                        status = random.random() < 0.85
                        db.add(attendance.Attendance(student_id=s.id, subject_id=sub.id, date=datetime.utcnow().date(), status=status))
                        
                        # Random marks
                        db.add(marks.Marks(
                            student_id=s.id, 
                            subject_id=sub.id, 
                            assessment_type=marks.AssessmentType.MID_TERM, 
                            score=random.randint(18, 28), 
                            total=30
                        ))

        db.commit()
        print("Done! Comprehensive student dataset generated successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_students()
