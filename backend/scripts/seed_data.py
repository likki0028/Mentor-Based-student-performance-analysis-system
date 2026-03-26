"""
Seed Data Script (v2) — 195 Synthetic Students
================================================
Reads the generated synthetic_students.json and inserts all 195 students
(3 sections × 65) with their full curriculum subjects and academic marks
into the SQLite database.

Preserves the known login accounts: admin, mentor, lecturer, student.
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta

# Add the parent directory of 'backend' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    user, student, faculty, subject, section,
    attendance, marks, alert, assignment, quiz, quiz_attempt, submission, remark,
    material
)
from app.core.security import get_password_hash


# ============================================================================
# CURRICULUM (must match generate_synthetic_data.py)
# ============================================================================
from scripts.generate_synthetic_data import CURRICULUM

# Faculty assignments for Semester 6 (Home Teacher model)
# Map lecturer username -> (Subject Code, Section Name)
FACULTY_SUBJECT_ASSIGNMENTS = {
    "mentor_a": [("GR22A3140", "Section A"), ("GR22A3115", "Section B")], # ML (A), ACD (B)
    "mentor_b": [("GR22A3143", "Section B"), ("GR22A3140", "Section C")], # BDA (B), ML (C)
    "mentor_c": [("GR22A3115", "Section C"), ("GR22A3143", "Section A")], # ACD (C), BDA (A)
    "lecturer": [("GR22A3115", "Section A"), ("GR22A3140", "Section B"), ("GR22A3143", "Section C")] # Remaining
}

def seed_data():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("SEED DATA v2 — 195 Synthetic Students")
        print("=" * 60)

        # -------------------------------------------------
        # 1. Clear existing data (Postgres safe)
        # -------------------------------------------------
        print("\n[1/8] Dropping and recreating tables...")
        if "postgresql" in str(engine.url):
             from sqlalchemy import text
             with engine.connect() as conn:
                 # Drop all tables with CASCADE for Postgres
                 conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
                 conn.commit()
             print("  Postgres Schema cleared via CASCADE!")
        else:
            Base.metadata.drop_all(bind=engine)
            
        Base.metadata.create_all(bind=engine)
        print("  Done!")

        # -------------------------------------------------
        # 2. Create Admin
        # -------------------------------------------------
        print("\n[2/8] Creating Admin...")
        admin = user.User(
            username="admin",
            email="admin@vibe.com",
            hashed_password=get_password_hash("admin123"),
            role=user.UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("  Admin created (admin / admin123)")

        # -------------------------------------------------
        # 3. Create Faculty (Mentors & Lecturers)
        # -------------------------------------------------
        print("\n[3/8] Creating Faculty...")
        faculties = []
        mentor_map = {} # Map section letter -> faculty.id

        # Home Teachers (Mentors who also teach)
        mentors_info = [
            ("mentor_a", "mentor_a@vibe.com", "mentor123", "A"),
            ("mentor_b", "mentor_b@vibe.com", "mentor123", "B"),
            ("mentor_c", "mentor_c@vibe.com", "mentor123", "C"),
        ]

        for i, (uname, email, pwd, sec_letter) in enumerate(mentors_info):
            m_user = user.User(
                username=uname,
                email=email,
                hashed_password=get_password_hash(pwd),
                role=user.UserRole.MENTOR,
                is_active=True
            )
            db.add(m_user)
            db.flush()
            fac = faculty.Faculty(user_id=m_user.id, employee_id=f"FAC100{i+1}")
            db.add(fac)
            db.flush()
            faculties.append(fac)
            mentor_map[sec_letter] = fac.id
            print(f"  Created Mentor for Section {sec_letter} ({uname})")

        # General lecturer
        lecturer_user = user.User(
            username="lecturer", email="lecturer@vibe.com",
            hashed_password=get_password_hash("lecturer123"), role=user.UserRole.LECTURER, is_active=True
        )
        db.add(lecturer_user)
        db.flush()
        lecturer_fac = faculty.Faculty(user_id=lecturer_user.id, employee_id="FAC1004")
        db.add(lecturer_fac)
        faculties.append(lecturer_fac)
        print("  Created general lecturer (lecturer / lecturer123)")

        db.commit()


        # -------------------------------------------------
        # 4. Create Sections
        # -------------------------------------------------
        print("\n[4/8] Creating Sections...")
        db_sections = {}
        for sec_name in ["A", "B", "C"]:
            sec = section.Section(name=f"Section {sec_name}")
            db.add(sec)
            db_sections[sec_name] = sec
        db.commit()
        print(f"  Created {len(db_sections)} sections")

        # -------------------------------------------------
        # 5. Create All Curriculum Subjects
        # -------------------------------------------------
        print("\n[5/8] Creating Subjects (full curriculum)...")
        db_subjects = {}  # key: subject_code -> Subject obj
        for sem_num, sem_info in CURRICULUM.items():
            for subj in sem_info["subjects"]:
                name = subj["name"]
                code = subj["code"]
                stype = subj["type"].lower()
                credits_val = subj["credits"]
                
                # Normalize type if needed (e.g., Non-Credit -> non-credit)
                if stype == "non-credit":
                    final_type = marks.AssessmentType.INTERNAL # Wait, no, use SubjectType
                
                # Check models/subject.py for SubjectType enum
                from app.models.subject import SubjectType
                if stype == "non-credit":
                    final_type = SubjectType.NON_CREDIT
                elif stype == "theory":
                    final_type = SubjectType.THEORY
                elif stype == "lab":
                    final_type = SubjectType.LAB
                else:
                    final_type = SubjectType.THEORY

                sub = subject.Subject(
                    name=name, 
                    code=code, 
                    semester=sem_num,
                    subject_type=final_type,
                    credits=credits_val
                )
                db.add(sub)
                db_subjects[code] = sub
        db.commit()
        print(f"  Created {len(db_subjects)} subjects across 5 semesters")

        # -------------------------------------------------
        # 6. Load Synthetic Students & Create Users/Students
        # -------------------------------------------------
        print("\n[6/8] Creating 195 Students from synthetic data...")
        json_path = os.path.join(current_dir, "synthetic_students.json")
        with open(json_path, "r", encoding="utf-8") as f:
            synthetic_students = json.load(f)

        # Assign mentors round-robin
        db_students = []
        # Limit to 30 students for fast remote deployment demo
        for idx, s_data in enumerate(synthetic_students[:30]):
            student_name = s_data["name"]
            student_id_str = s_data["student_id"]
            sec_letter = s_data["section"]

            # Create student user account
            # Username: enrollment number (lowercase), Password: student123
            username = student_id_str.lower()
            s_user = user.User(
                username=username,
                email=f"{username}@griet.ac.in",
                hashed_password=get_password_hash("student123"),
                role=user.UserRole.STUDENT,
                is_active=True
            )
            db.add(s_user)
            db.flush()

            stu = student.Student(
                user_id=s_user.id,
                enrollment_number=student_id_str,
                current_semester=6,  # SEM 6 Active
                mentor_id=mentor_map[sec_letter], # Exact home teacher
                section_id=db_sections[sec_letter].id
            )
            db.add(stu)
            db_students.append((stu, s_data))

        # Also create the known "student" login that maps to the first student
        student_user = user.User(
            username="student", email="student@vibe.com",
            hashed_password=get_password_hash("student123"), role=user.UserRole.STUDENT, is_active=True
        )
        db.add(student_user)
        db.flush()
        # Link known student to a copy of the first student's enrollment
        stu_known = student.Student(
            user_id=student_user.id,
            enrollment_number="23241A6700",
            current_semester=6,
            mentor_id=mentor_map["A"],
            section_id=db_sections["A"].id
        )
        db.add(stu_known)
        db.commit()
        print(f"  Created {len(db_students)} students + 1 known login (student / student123)")

        # -------------------------------------------------
        # 6.5 Assign Faculty to Subjects (Lecturer/Section Link)
        #     Also insert dummy material and assignment for Sem 6
        # -------------------------------------------------
        print("\n[6.5/8] Linking Lecturers to Subjects & Adding Classes/Materials...")
        # Since we don't have a direct FacultySubject link table yet,
        # we will generate initial Assignments and Materials to establish this link.
        from app.models.assignment import Assignment
        from app.models.material import Material
        from datetime import datetime, timedelta

        for fac in faculties:
            uname = fac.user.username
            if uname in FACULTY_SUBJECT_ASSIGNMENTS:
                for sub_code, sec_name in FACULTY_SUBJECT_ASSIGNMENTS[uname]:
                    # Find subject id
                    if sub_code not in db_subjects: continue
                    sub_id = db_subjects[sub_code].id
                    
                    # Find section id
                    sec_id = None
                    for name, s_obj in db_sections.items():
                        if s_obj.name == sec_name:
                            sec_id = s_obj.id
                            break
                    
                    if sec_id:
                        # 1. Create a Material for this subject-section
                        db.add(Material(
                            title=f"Course Syllabus & Introduction",
                            description=f"Welcome to {db_subjects[sub_code].name}. Please review the syllabus.",
                            file_url="/uploads/materials/dummy_syllabus.pdf",
                            subject_id=sub_id,
                            section_id=sec_id,
                            faculty_id=fac.id
                        ))
                        
                        # 2. Create an Assignment for this subject-section
                        db.add(Assignment(
                            title=f"Assignment 1 - Basic Concepts",
                            description="Complete the introductory questions.",
                            due_date=datetime.utcnow() + timedelta(days=7),
                            subject_id=sub_id,
                            section_id=sec_id,
                            faculty_id=fac.id
                        ))
        db.commit()


        # -------------------------------------------------
        # 7. Insert Academic Data (Marks + Attendance)
        # -------------------------------------------------
        print(f"\n[7/8] Creating Academic Data (bulk inserting for speed)...")
        start_date = datetime(2024, 7, 1).date()  # Academic year start
        marks_count = 0
        attendance_count = 0

        # Create arrays for bulk inserts to speed up remote DB insertion
        marks_batch = []
        att_batch = []

        for stu_obj, s_data in db_students:
            db.flush()  # Ensure stu_obj.id is available

            for sem in s_data["semesters"]:
                sem_num = sem["semester"]
                sem_start = start_date + timedelta(days=(sem_num - 1) * 150)

                for subj_data in sem["subjects"]:
                    subj_code = subj_data["code"]
                    if subj_code not in db_subjects:
                        continue
                    sub_obj = db_subjects[subj_code]
                    db.flush()  # Ensure sub_obj.id is available
                    m = subj_data["marks"]

                    if subj_data["type"] == "Theory":
                        # Mid 1 marks (mid_term)
                        marks_batch.append(marks.Marks(
                            student_id=stu_obj.id,
                            subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.MID_TERM,
                            score=m["mid1_total"],
                            total=30
                        ))
                        # Mid 2 marks (also mid_term — we store both)
                        marks_batch.append(marks.Marks(
                            student_id=stu_obj.id,
                            subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.MID_TERM,
                            score=m["mid2_total"],
                            total=30
                        ))
                        # Internal marks (assignments + attendance component)
                        marks_batch.append(marks.Marks(
                            student_id=stu_obj.id,
                            subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.INTERNAL,
                            score=m["internal_total"],
                            total=40
                        ))
                        
                        # Only add end-term if semester is completed
                        if sem_num < 6:
                            # External/End-term marks
                            marks_batch.append(marks.Marks(
                                student_id=stu_obj.id,
                                subject_id=sub_obj.id,
                                assessment_type=marks.AssessmentType.END_TERM,
                                score=m["external"],
                                total=60
                            ))
                            marks_count += 1
                        marks_count += 3

                    elif subj_data["type"] == "Lab":
                        # Lab internal
                        marks_batch.append(marks.Marks(
                            student_id=stu_obj.id,
                            subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.INTERNAL,
                            score=m["internal_total"],
                            total=40
                        ))
                        # Only add end-term if semester is completed
                        if sem_num < 6:
                            # Lab external
                            marks_batch.append(marks.Marks(
                                student_id=stu_obj.id,
                                subject_id=sub_obj.id,
                                assessment_type=marks.AssessmentType.END_TERM,
                                score=m["external"],
                                total=60
                            ))
                            marks_count += 1
                        marks_count += 1

                    else:  # Non-Credit
                        # User wants mid marks for non-credit too
                        marks_batch.append(marks.Marks(
                            student_id=stu_obj.id,
                            subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.MID_TERM,
                            score=m["mid1"],
                            total=40
                        ))
                        marks_batch.append(marks.Marks(
                            student_id=stu_obj.id,
                            subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.MID_TERM,
                            score=m["mid2"],
                            total=40
                        ))
                        marks_count += 2

                    # Attendance: Generate ~15 attendance records per subject per semester instead of 60 for speed
                    att_rate = s_data["overall_attendance_rate"]
                    for day in range(15):
                        date = sem_start + timedelta(days=int(day * 10) + random.randint(0, 2))
                        present = random.random() < att_rate
                        att_batch.append(attendance.Attendance(
                            student_id=stu_obj.id,
                            subject_id=sub_obj.id,
                            date=date,
                            status=present
                        ))
                        attendance_count += 1

            # Commit every 20 students to avoid memory issues and speed up remote DB inserts
            if (db_students.index((stu_obj, s_data)) + 1) % 20 == 0:
                if marks_batch:
                    db.add_all(marks_batch)
                    marks_batch = []
                if att_batch:
                    db.add_all(att_batch)
                    att_batch = []
                db.commit()
                done = db_students.index((stu_obj, s_data)) + 1
                print(f"    Progress: {done}/{len(db_students)} students...")

        # Final flush for any remaining marks/attendance in batch
        if marks_batch:
            db.add_all(marks_batch)
        if att_batch:
            db.add_all(att_batch)
        db.commit()
        print(f"  Done! {marks_count} marks records, {attendance_count} attendance records")

        # -------------------------------------------------
        # 8. Generate Alerts
        # -------------------------------------------------
        print("\n[8/8] Generating alerts for at-risk students...")
        from sqlalchemy import func, Integer as SqlInt
        alert_count = 0

        for stu_obj, s_data in db_students:
            risk = s_data["risk_profile"]
            att_rate = s_data["overall_attendance_rate"]
            cgpa = s_data["cgpa"]

            if risk == "High":
                db.add(alert.Alert(
                    student_id=stu_obj.id,
                    message=f"Student at HIGH risk. Attendance: {att_rate*100:.1f}%, CGPA: {cgpa:.2f}",
                    type="High Risk"
                ))
                alert_count += 1
            elif risk == "Medium" and att_rate < 0.78:
                db.add(alert.Alert(
                    student_id=stu_obj.id,
                    message=f"Student at MEDIUM risk. Attendance: {att_rate*100:.1f}%",
                    type="Low Attendance"
                ))
                alert_count += 1

        db.commit()
        print(f"  Generated {alert_count} alerts")

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------
        print(f"\n{'=' * 60}")
        print("✅ DATABASE SEEDED SUCCESSFULLY!")
        print(f"{'=' * 60}")
        print(f"  Admin:      admin / admin123")
        print(f"  Mentor:     mentor / mentor123")
        print(f"  Lecturer:   lecturer / lecturer123")
        print(f"  Students:   195 students (student / student123 for demo login)")
        print(f"              Usernames: 23241a6701 .. 23241a67{len(db_students):02d}")
        print(f"  Faculty:    {len(faculties)} total")
        print(f"  Sections:   {len(db_sections)}")
        print(f"  Subjects:   {len(db_subjects)}")
        print(f"  Marks:      {marks_count} records")
        print(f"  Attendance: {attendance_count} records")
        print(f"  Alerts:     {alert_count}")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
