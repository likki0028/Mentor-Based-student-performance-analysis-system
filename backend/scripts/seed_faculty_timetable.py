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
            ("Dr. M. V. Rama Sundari", "1741", "ramasundari"),
            ("Ms. D. Priyanka", "1848", "priyanka"),
            ("Dr. M. Kiran Kumar", "1610", "kirankumar"),
            ("Dr. R. P. Ram Kumar", "1695", "ramkumar"),
            ("Ms. P. Lakshmi Sruthi", "1739", "lakshmisruthi"),
            ("Dr. J. Sasi Bhanu", "1875", "sasibhanu"),
            ("Ms. V. Sreevani", "1724", "sreevani"),
            ("Ms. Manu Hajari", "1772", "manuhajari"),
            ("Ms. B. Saritha", "1862", "saritha_b"),
            ("Ms. K. Tejasvi", "1836", "tejasvi"),
            ("Ms. S. H. Swaroopa", "1878", "swaroopa"),
            ("Ms. Y.P.S.S.V. MOHANA", "1822", "mohana"),
            ("Ms. K. Kalpana", "1769", "kalpana"),
            ("Ms. S. Srilatha", "1837", "srilatha"),
            ("Mr. VSRK Raju", "1806", "vsrkraju"),
            ("Mr. K. Mallikarjuna Raju", "1726", "mallikarjuna"),
            ("Ms. Rashi Saxena", "1770", "rashisaxena"),
            ("Ms. D. S. Niharika", "1838", "niharika"),
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

        # Also map the demo 'lecturer' account to Dr. M. V. Rama Sundari's work for testing
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
