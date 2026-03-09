import sys
import os
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
    attendance, marks, alert, assignment, quiz, quiz_attempt, submission, remark
)

def seed_data():
    db = SessionLocal()
    try:
        print("Starting data seeding...")

        # 1. Clear existing data
        print("Clearing existing data...")
        db.query(remark.Remark).delete()
        db.query(alert.Alert).delete()
        db.query(quiz_attempt.QuizAttempt).delete()
        db.query(quiz.Quiz).delete()
        db.query(submission.Submission).delete()
        db.query(assignment.Assignment).delete()
        db.query(marks.Marks).delete()
        db.query(attendance.Attendance).delete()
        db.query(student.Student).delete()
        db.query(faculty.Faculty).delete()
        db.query(section.Section).delete()
        db.query(subject.Subject).delete()
        db.query(user.User).delete()
        db.commit()

        # 2. Create Admin
        print("Creating Admin...")
        admin = user.User(
            username="admin",
            email="admin@vibe.com",
            hashed_password="admin123",
            role=user.UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()

        # 3. Create Subjects
        print("Creating Subjects...")
        subjects_list = [
            ("Data Structures", "CS201"),
            ("Algorithms", "CS202"),
            ("Database Systems", "CS203"),
            ("Operating Systems", "CS301"),
            ("Computer Networks", "CS302"),
            ("Machine Learning", "CS401"),
        ]
        db_subjects = []
        for name, code in subjects_list:
            sub = subject.Subject(name=name, code=code)
            db.add(sub)
            db_subjects.append(sub)
        db.commit()

        # 4. Create Known Faculty Users
        print("Creating Faculty...")
        faculties = []

        # Known mentor user
        mentor_user = user.User(
            username="mentor",
            email="mentor@vibe.com",
            hashed_password="mentor123",
            role=user.UserRole.MENTOR,
            is_active=True
        )
        db.add(mentor_user)
        db.flush()
        mentor_fac = faculty.Faculty(user_id=mentor_user.id, employee_id="FAC1001")
        db.add(mentor_fac)
        faculties.append(mentor_fac)

        # Known lecturer user
        lecturer_user = user.User(
            username="lecturer",
            email="lecturer@vibe.com",
            hashed_password="lecturer123",
            role=user.UserRole.LECTURER,
            is_active=True
        )
        db.add(lecturer_user)
        db.flush()
        lecturer_fac = faculty.Faculty(user_id=lecturer_user.id, employee_id="FAC1002")
        db.add(lecturer_fac)
        faculties.append(lecturer_fac)

        # Additional faculty
        extra_faculty_names = ["Dr. Sharma", "Prof. Patel", "Dr. Rao", "Prof. Gupta", "Dr. Kumar"]
        for i, name in enumerate(extra_faculty_names):
            f_user = user.User(
                username=name.lower().replace(" ", "_").replace(".", ""),
                email=f"faculty{i+3}@vibe.com",
                hashed_password="faculty123",
                role=user.UserRole.MENTOR,
                is_active=True
            )
            db.add(f_user)
            db.flush()
            fac = faculty.Faculty(
                user_id=f_user.id,
                employee_id=f"FAC{1003+i}"
            )
            db.add(fac)
            faculties.append(fac)
        db.commit()

        # 5. Create Sections
        print("Creating Sections...")
        sections_list = ["Section A", "Section B", "Section C"]
        db_sections = []
        for name in sections_list:
            sec = section.Section(name=name)
            db.add(sec)
            db_sections.append(sec)
        db.commit()

        # 6. Create Students (including a known 'student' user)
        print("Creating Students...")
        students = []

        # Known student user (username: "student")
        student_user = user.User(
            username="student",
            email="student@vibe.com",
            hashed_password="student123",
            role=user.UserRole.STUDENT,
            is_active=True
        )
        db.add(student_user)
        db.flush()
        stu_known = student.Student(
            user_id=student_user.id,
            enrollment_number="2024CS1000",
            current_semester=3,
            mentor_id=faculties[0].id  # Assign to first mentor
        )
        db.add(stu_known)
        students.append(stu_known)

        # 50 additional students
        student_names = [
            "Aarav", "Vivaan", "Aditya", "Sai", "Arjun", "Reyansh", "Ayaan",
            "Krishna", "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav",
            "Advaith", "Kabir", "Dhruv", "Ritvik", "Aarush", "Vihaan", "Ananya",
            "Diya", "Myra", "Sara", "Aarohi", "Anika", "Navya", "Kiara",
            "Prisha", "Aadhya", "Kavya", "Meera", "Riya", "Zara", "Ishita",
            "Sanya", "Tara", "Nisha", "Pooja", "Simran", "Neha", "Rohan",
            "Raj", "Dev", "Vikram", "Aryan", "Karthik", "Manish", "Suresh",
            "Amit", "Rahul"
        ]

        for i in range(50):
            s_user = user.User(
                username=f"student{i+1}",
                email=f"student{i+1}@vibe.com",
                hashed_password="student123",
                role=user.UserRole.STUDENT,
                is_active=True
            )
            db.add(s_user)
            db.flush()

            stu = student.Student(
                user_id=s_user.id,
                enrollment_number=f"2024CS{1001+i}",
                current_semester=random.choice([1, 2, 3, 4, 5, 6]),
                mentor_id=random.choice(faculties).id  # Random mentor assignment
            )
            db.add(stu)
            students.append(stu)
        db.commit()

        # 7. Create Academic Data
        print("Creating Academic Data...")
        start_date = datetime.now().date() - timedelta(days=90)

        for stu in students:
            # Attendance: varied patterns
            is_low_attendance = random.random() < 0.15  # 15% chance of low attendance
            
            for day in range(30):
                date = start_date + timedelta(days=day * 3)
                if is_low_attendance:
                    present_prob = random.choices([True, False], weights=[55, 45], k=1)[0]
                else:
                    present_prob = random.choices([True, False], weights=[85, 15], k=1)[0]

                for sub in db_subjects:
                    att = attendance.Attendance(
                        student_id=stu.id,
                        subject_id=sub.id,
                        date=date,
                        status=present_prob
                    )
                    db.add(att)

            # Marks: varied performance per subject
            is_weak = random.random() < 0.1  # 10% chance of weak student
            for sub in db_subjects:
                for assess_type in [marks.AssessmentType.MID_TERM, marks.AssessmentType.INTERNAL]:
                    if is_weak:
                        score = random.randint(15, 45)
                    else:
                        score = random.randint(40, 95)
                    
                    mark_entry = marks.Marks(
                        student_id=stu.id,
                        subject_id=sub.id,
                        assessment_type=assess_type,
                        score=score,
                        total=100
                    )
                    db.add(mark_entry)
        db.commit()

        # 8. Create Assignments
        print("Creating Assignments...")
        assignment_data = [
            ("Binary Tree Implementation", "Implement AVL tree with insert and delete operations", 1),
            ("Graph Algorithms", "Implement Dijkstra and BFS/DFS algorithms", 2),
            ("SQL Queries Project", "Design a database and write complex queries", 3),
            ("Process Scheduler", "Simulate Round Robin and FCFS scheduling", 4),
            ("Network Protocol Analysis", "Analyze TCP/IP packet captures using Wireshark", 5),
        ]
        for title, desc, sub_idx in assignment_data:
            a = assignment.Assignment(
                title=title,
                description=desc,
                due_date=datetime.now().date() + timedelta(days=random.randint(5, 30)),
                subject_id=sub_idx
            )
            db.add(a)
        db.commit()

        # 9. Create Quizzes
        print("Creating Quizzes...")
        quiz_data = [
            ("DS Mid-term Quiz", 1, 50),
            ("Algo Weekly Test", 2, 30),
            ("DBMS Concepts Quiz", 3, 40),
            ("OS Fundamentals", 4, 25),
        ]
        for title, sub_idx, total in quiz_data:
            q = quiz.Quiz(title=title, subject_id=sub_idx, total_marks=total)
            db.add(q)
        db.commit()

        # 10. Generate alerts for at-risk students
        print("Generating alerts...")
        from sqlalchemy import func, Integer as SqlInt
        for stu in students:
            total = db.query(func.count(attendance.Attendance.id)).filter(
                attendance.Attendance.student_id == stu.id
            ).scalar() or 0
            present = db.query(func.sum(
                func.cast(attendance.Attendance.status, SqlInt)
            )).filter(
                attendance.Attendance.student_id == stu.id
            ).scalar() or 0
            att_pct = (present / total * 100) if total > 0 else 100

            if att_pct < 75:
                db.add(alert.Alert(
                    student_id=stu.id,
                    message=f"Attendance is {att_pct:.1f}% (below 75% threshold)",
                    type="Low Attendance"
                ))

            avg_score = db.query(func.avg(marks.Marks.score)).filter(
                marks.Marks.student_id == stu.id
            ).scalar()
            if avg_score is not None and avg_score < 40:
                db.add(alert.Alert(
                    student_id=stu.id,
                    message=f"Average score is {avg_score:.1f}% (below 40% threshold)",
                    type="Low Marks"
                ))
        db.commit()

        print("\n✅ Database seeded successfully!")
        print(f"   - 1 Admin (admin / admin123)")
        print(f"   - 1 Mentor (mentor / mentor123)")
        print(f"   - 1 Lecturer (lecturer / lecturer123)")
        print(f"   - {len(faculties)-2} Additional Faculty (faculty123)")
        print(f"   - 1 Known Student (student / student123)")
        print(f"   - 50 Students (student1..student50 / student123)")
        print(f"   - {len(db_subjects)} Subjects")
        print(f"   - Academic data generated for all students")

    except Exception as e:
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
