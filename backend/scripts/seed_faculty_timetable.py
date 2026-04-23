import sys
import os

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

def seed_timetable():
    db = SessionLocal()
    try:
        print("SEEDING DEPARTMENT TIMETABLE...")
        
        # Create tables if they don't exist (important for the new FacultyAssignment table)
        Base.metadata.create_all(bind=engine)
        
        # Ensure Sections exist
        sections_map = {}
        for s_name in ["Section A", "Section B", "Section C"]:
            sec = db.query(section.Section).filter(section.Section.name == s_name).first()
            if not sec:
                sec = section.Section(name=s_name)
                db.add(sec)
                db.flush()
            sections_map[s_name] = sec

        # Ensure Subjects exist
        subjects_data = [
            ("Machine Learning", "GR22A3140"),
            ("Machine Learning Lab", "GR22A3142"),
            ("Automata and Compiler Design", "GR22A3115"),
            ("Big Data Analytics", "GR22A3143"),
            ("Big Data Analytics Lab", "GR22A3148"),
            ("Cryptography and Network Security", "GR22A4048"),
            ("Joy of Computing using Python", "NPTEL"),
            ("Mini Project with Seminar", "GR22A3089"),
            ("Constitution of India", "GR22A2003"),
        ]
        subjects_map = {}
        for name, code in subjects_data:
            sub = db.query(subject.Subject).filter(subject.Subject.code == code).first()
            if not sub:
                sub = subject.Subject(name=name, code=code, semester=6, credits=3)
                db.add(sub)
                db.flush()
            subjects_map[code] = sub

        # Faculty Data (Name, Employee ID, Username)
        faculty_raw = [
            ("Faculty 1", "1741", "faculty1"),
            ("Faculty 2", "1848", "faculty2"),
            ("Faculty 3", "1610", "faculty3"),
            ("Faculty 4", "1695", "faculty4"),
            ("Faculty 5", "1739", "faculty5"),
            ("Faculty 6", "1875", "faculty6"),
            ("Faculty 7", "1724", "faculty7"),
            ("Faculty 8", "1772", "faculty8"),
            ("Faculty 9", "1862", "faculty9"),
            ("Faculty 10", "1836", "faculty10"),
            ("Faculty 11", "1878", "faculty11"),
            ("Faculty 12", "1822", "faculty12"),
            ("Faculty 13", "1769", "faculty13"),
            ("Faculty 14", "1837", "faculty14"),
            ("Faculty 15", "1806", "faculty15"),
            ("Faculty 16", "1726", "faculty16"),
            ("Faculty 17", "1770", "faculty17"),
            ("Faculty 18", "1838", "faculty18"),
        ]
        
        faculty_map = {}
        for name, emp_id, uname in faculty_raw:
            u = db.query(user.User).filter(user.User.username == uname).first()
            if not u:
                u = user.User(username=uname, hashed_password=get_password_hash("staff123"), role=user.UserRole.LECTURER)
                db.add(u)
                db.flush()
            
            f = db.query(faculty.Faculty).filter(faculty.Faculty.user_id == u.id).first()
            if not f:
                f = faculty.Faculty(user_id=u.id, employee_id=emp_id)
                db.add(f)
                db.flush()
            faculty_map[emp_id] = f

        # Also map the demo 'lecturer' account to Faculty 1's work for testing
        demo_lecturer = db.query(faculty.Faculty).filter(faculty.Faculty.employee_id == "FAC002").first()
        if demo_lecturer:
             # We'll use the 'lecturer' account as a stand-in for Section A ML
             faculty_map['DEMO_LECT'] = demo_lecturer

        # Assignments (Subject Code, Section Name, Faculty EMP IDs)
        mappings = [
            # SEC A
            ("GR22A3140", "Section A", ["1741"]),
            ("GR22A3142", "Section A", ["1741", "1769"]),
            ("GR22A3115", "Section A", ["1848"]),
            ("GR22A3143", "Section A", ["1610"]),
            ("GR22A3148", "Section A", ["1610", "1837"]),
            ("GR22A4048", "Section A", ["1695"]),
            ("NPTEL", "Section A", ["1739"]),
            ("GR22A3089", "Section A", ["1806", "1862"]),
            ("GR22A2003", "Section A", ["1836"]),

            # SEC B
            ("GR22A3140", "Section B", ["1875"]),
            ("GR22A3142", "Section B", ["1875", "1769"]),
            ("GR22A3115", "Section B", ["1848"]),
            ("GR22A3143", "Section B", ["1724"]),
            ("GR22A3148", "Section B", ["1724", "1726"]),
            ("GR22A4048", "Section B", ["1772"]),
            ("NPTEL", "Section B", ["1862"]),
            ("GR22A3089", "Section B", ["1806", "1838"]),
            ("GR22A2003", "Section B", ["1836"]),

            # SEC C
            ("GR22A3140", "Section C", ["1875"]),
            ("GR22A3142", "Section C", ["1875", "1878"]),
            ("GR22A3115", "Section C", ["1878"]),
            ("GR22A3143", "Section C", ["1724"]),
            ("GR22A3148", "Section C", ["1724", "1726"]),
            ("GR22A4048", "Section C", ["1772"]),
            ("NPTEL", "Section C", ["1837"]),
            ("GR22A3089", "Section C", ["1806", "1837"]),
            ("GR22A2003", "Section C", ["1822"]),
        ]

        print("Creating assignments...")
        for sub_code, sec_name, emp_ids in mappings:
            sub = subjects_map[sub_code]
            sec = sections_map[sec_name]
            for eid in emp_ids:
                f = faculty_map[eid]
                # Check if exists
                existing = db.query(faculty.FacultyAssignment).filter(
                    faculty.FacultyAssignment.faculty_id == f.id,
                    faculty.FacultyAssignment.subject_id == sub.id,
                    faculty.FacultyAssignment.section_id == sec.id
                ).first()
                if not existing:
                    db.add(faculty.FacultyAssignment(faculty_id=f.id, subject_id=sub.id, section_id=sec.id))
        
        # Add demo lecturer assignment for visibility
        if 'DEMO_LECT' in faculty_map:
            sub_ml = subjects_map["GR22A3140"]
            sec_a = sections_map["Section A"]
            db.add(faculty.FacultyAssignment(faculty_id=faculty_map['DEMO_LECT'].id, subject_id=sub_ml.id, section_id=sec_a.id))

        db.commit()
        print("Done! Seeding completed successfully.")

    except Exception as e:
        db.rollback()
        import traceback
        with open("seeding_error.txt", "w") as f:
            traceback.print_exc(file=f)
        print("Error during seeding. See seeding_error.txt for details.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_timetable()
