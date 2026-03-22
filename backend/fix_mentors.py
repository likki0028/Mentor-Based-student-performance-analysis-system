
import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime

# Add the parent directory of 'backend' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.database import SessionLocal
from app.models import user as user_model
from app.models import faculty as faculty_model
from app.models import student as student_model
from app.models import section as section_model
from app.models import subject as subject_model
from app.core.security import get_password_hash

def fix_mentors():
    db = SessionLocal()
    try:
        print("Checking for missing mentors...")
        
        # 1. Ensure mentor_b and mentor_c users exist
        mentors_to_create = [
            ("mentor_b", "mentor_b@vibe.com", "B"),
            ("mentor_c", "mentor_c@vibe.com", "C"),
        ]
        
        for username, email, section_name in mentors_to_create:
            existing_user = db.query(user_model.User).filter(user_model.User.username == username).first()
            if not existing_user:
                print(f"  Creating user {username}...")
                new_user = user_model.User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash("mentor123"),
                    role=user_model.UserRole.MENTOR,
                    is_active=True
                )
                db.add(new_user)
                db.flush()
                
                # Create Faculty record
                fac = faculty_model.Faculty(user_id=new_user.id, employee_id=f"FIX_{username.upper()}")
                db.add(fac)
                db.flush()
                print(f"  Created Faculty record for {username} (ID: {fac.id})")
            else:
                print(f"  User {username} already exists.")
                fac = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.user_id == existing_user.id).first()
                if not fac:
                    fac = faculty_model.Faculty(user_id=existing_user.id, employee_id=f"FIX_{username.upper()}")
                    db.add(fac)
                    db.flush()
                    print(f"  Created missing Faculty record for existing user {username}")

            # 2. Map students of the section to this mentor
            # Section IDs: B=2, C=3 (based on previous check)
            sec_id = 2 if section_name == "B" else 3
            students = db.query(student_model.Student).filter(student_model.Student.section_id == sec_id).all()
            for s in students:
                s.mentor_id = fac.id
            print(f"  Linked {len(students)} students in Section {section_name} to {username}")

        # 3. Handle FacultyAssignments (for subjects)
        # mentor_b: BDA (GR22A3143, Sec 2), ML (GR22A3140, Sec 3)
        # mentor_c: ACD (GR22A3115, Sec 3), BDA (GR22A3143, Sec 1)
        
        assignments = [
            ("mentor_b", "GR22A3143", 2), # BDA in Section B
            ("mentor_b", "GR22A3140", 3), # ML in Section C
            ("mentor_c", "GR22A3115", 3), # ACD in Section C
            ("mentor_c", "GR22A3143", 1), # BDA in Section A
        ]
        
        for uname, sub_code, s_id in assignments:
            u = db.query(user_model.User).filter(user_model.User.username == uname).first()
            f = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.user_id == u.id).first()
            s = db.query(subject_model.Subject).filter(subject_model.Subject.code == sub_code).first()
            if f and s:
                # Check for existing assignment
                existing_fa = db.query(faculty_model.FacultyAssignment).filter(
                    faculty_model.FacultyAssignment.faculty_id == f.id,
                    faculty_model.FacultyAssignment.subject_id == s.id,
                    faculty_model.FacultyAssignment.section_id == s_id
                ).first()
                if not existing_fa:
                    new_fa = faculty_model.FacultyAssignment(
                        faculty_id=f.id,
                        subject_id=s.id,
                        section_id=s_id
                    )
                    db.add(new_fa)
                    print(f"  Added FacultyAssignment: {uname} -> {sub_code} (Section {s_id})")
        
        db.commit()
        print("\nFix completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during fix: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_mentors()
