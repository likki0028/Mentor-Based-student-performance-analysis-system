"""
Seed Section B Only - Quick & Working
======================================
65 students, real faculty, timetable-based attendance, marks, assignments.
"""
import sys, os, json, random
from datetime import datetime, timedelta, date

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.faculty import Faculty, FacultyAssignment
from app.models.subject import Subject, SubjectType
from app.models.section import Section
from app.models.attendance import Attendance
from app.models.marks import Marks, AssessmentType
from app.models.alert import Alert
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.remark import Remark
from app.models.material import Material
from app.models.syllabus_topic import SyllabusTopic
from app.models.doubt import Doubt
from app.models.doubt_comment import DoubtComment
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_response import QuizResponse
from app.models.mark_finalization import MarkFinalization
from app.core.security import get_password_hash

random.seed(42)

# ---- SECTION B TIMETABLE ----
TIMETABLE_B = {
    "MON": ["NPTEL", "ML LAB", "ML LAB", "ML LAB", "ACD", "ACD", "CNS"],
    "TUE": ["CNS", "MP", "MP", "MP", "BDA", "BDA", "NPTEL"],
    "WED": ["COI", "BDA LAB", "BDA LAB", "BDA LAB", "ML", "ML", "ML"],
    "THU": ["CNS", "BDA", "ML", "ML", "ACD", "COI", "COI"],
    "FRI": ["TRAINING"] * 7,
    "SAT": ["ACD", "ACD", "ACD", "BDA", "CNS", "CNS", "ML"],
}

SHORT_TO_CODE = {
    "ML": "GR22A3140", "ACD": "GR22A3115", "BDA": "GR22A3143",
    "CNS": "GR22A4048", "NPTEL": "NPTEL",
    "ML LAB": "GR22A3142", "BDA LAB": "GR22A3148",
    "MP": "GR22A3089", "COI": "GR22A2003",
}

WEEKDAY_MAP = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT"}
SEM_START = date(2025, 12, 12)
SIM_DATE = date(2026, 3, 21)
VAC_START, VAC_END = date(2026, 1, 12), date(2026, 1, 17)
MID1_START, MID1_END = date(2026, 2, 19), date(2026, 2, 21)

def is_holiday(d):
    if d.weekday() == 6: return True
    if VAC_START <= d <= VAC_END: return True
    if MID1_START <= d <= MID1_END: return True
    return False

def get_subjects_for_day(day_name):
    if day_name not in TIMETABLE_B: return set()
    codes = set()
    for short in TIMETABLE_B[day_name]:
        if short and short != "TRAINING":
            c = SHORT_TO_CODE.get(short)
            if c: codes.add(c)
    return codes

# ---- SUBJECTS SEM 6 ----
SEM6_SUBJECTS = [
    ("Machine Learning", "GR22A3140", 3, "THEORY"),
    ("Automata and Compiler Design", "GR22A3115", 3, "THEORY"),
    ("Big Data Analytics", "GR22A3143", 3, "THEORY"),
    ("Cryptography and Network Security", "GR22A4048", 3, "THEORY"),
    ("Joy of Computing using Python", "NPTEL", 3, "NPTEL"),
    ("Machine Learning Lab", "GR22A3142", 1.5, "LAB"),
    ("Big Data Analytics Lab", "GR22A3148", 1.5, "LAB"),
    ("Mini Project with Seminar", "GR22A3089", 2, "LAB"),
    ("Constitution of India", "GR22A2003", 0, "NON_CREDIT"),
]

# ---- HISTORICAL SUBJECTS (Sem 1-5) ----
HISTORICAL_SUBJECTS = {
    1: [
        ("Engineering Mathematics - I", "MA101", 4, "THEORY"),
        ("Engineering Physics", "PH102", 3, "THEORY"),
        ("Engineering Chemistry", "CH103", 3, "THEORY"),
        ("Programming for Problem Solving", "CS104", 3, "THEORY"),
        ("Engineering Drawing", "ME105", 3, "THEORY"),
        ("Engineering Physics Lab", "PH106", 1.5, "LAB"),
        ("Programming Lab", "CS107", 1.5, "LAB"),
    ],
    2: [
        ("Engineering Mathematics - II", "MA201", 4, "THEORY"),
        ("Applied Physics", "PH202", 3, "THEORY"),
        ("Data Structures", "CS203", 3, "THEORY"),
        ("Digital Logic Design", "EC204", 3, "THEORY"),
        ("English Communication Skills", "EN205", 3, "THEORY"),
        ("Data Structures Lab", "CS206", 1.5, "LAB"),
        ("Digital Logic Lab", "EC207", 1.5, "LAB"),
    ],
    3: [
        ("Probability and Statistics", "MA301", 4, "THEORY"),
        ("Object Oriented Programming", "CS302", 3, "THEORY"),
        ("Computer Organization", "CS303", 3, "THEORY"),
        ("Discrete Mathematics", "CS304", 3, "THEORY"),
        ("Database Management Systems", "CS305", 3, "THEORY"),
        ("OOP Lab", "CS306", 1.5, "LAB"),
        ("DBMS Lab", "CS307", 1.5, "LAB"),
    ],
    4: [
        ("Operating Systems", "CS401", 3, "THEORY"),
        ("Computer Networks", "CS402", 3, "THEORY"),
        ("Software Engineering", "CS403", 3, "THEORY"),
        ("Design and Analysis of Algorithms", "CS404", 3, "THEORY"),
        ("Formal Languages and Automata", "CS405", 3, "THEORY"),
        ("Operating Systems Lab", "CS406", 1.5, "LAB"),
        ("Computer Networks Lab", "CS407", 1.5, "LAB"),
    ],
    5: [
        ("Artificial Intelligence", "CS501", 3, "THEORY"),
        ("Web Technologies", "CS502", 3, "THEORY"),
        ("Information Security", "CS503", 3, "THEORY"),
        ("Cloud Computing", "CS504", 3, "THEORY"),
        ("Data Mining", "CS505", 3, "THEORY"),
        ("Web Technologies Lab", "CS506", 1.5, "LAB"),
        ("AI Lab", "CS507", 1.5, "LAB"),
    ],
}


# ---- FACULTY SEC B ----
FACULTY_B = [
    ("Dr. J. Sasi Bhanu", "1875", "sasibhanu", [("GR22A3140", "ML"), ("GR22A3142", "ML LAB")]),
    ("Ms. D. Priyanka", "1848", "priyanka", [("GR22A3115", "ACD")]),
    ("Ms. V. Sreevani", "1724", "sreevani", [("GR22A3143", "BDA"), ("GR22A3148", "BDA LAB")]),
    ("Ms. Manu Hajari", "1772", "manuhajari", [("GR22A4048", "CNS")]),
    ("Ms. B. Saritha", "1862", "saritha_b", [("NPTEL", "JCP")]),
    ("Ms. K. Kalpana", "1769", "kalpana", [("GR22A3142", "ML LAB")]),
    ("Mr. K. Mallikarjuna Raju", "1726", "mallikarjuna", [("GR22A3148", "BDA LAB")]),
    ("Mr. VSRK Raju", "1806", "vsrkraju", [("GR22A3089", "MP")]),
    ("Ms. D. S. Niharika", "1838", "niharika", [("GR22A3089", "MP")]),  # Also class coordinator
    ("Ms. K. Tejasvi", "1836", "tejasvi", [("GR22A2003", "COI")]),
]

# Indian names
MALE_NAMES = ["Aarav","Aditya","Akash","Akhil","Amar","Amit","Anand","Anil","Ankit","Arjun","Arun","Ashwin","Bharat","Charan","Chirag","Deepak","Dhruv","Dinesh","Ganesh","Gaurav","Harsh","Hemant","Jayesh","Karan","Kartik","Kiran","Krishna","Kunal","Lokesh","Manoj","Mohan","Mukesh","Naveen","Nikhil","Pavan","Pranav","Prasad","Rahul","Raj","Rajesh"]
FEMALE_NAMES = ["Aishwarya","Amrutha","Anjali","Ananya","Bhavana","Chaitra","Deepika","Divya","Gayathri","Harini","Ishitha","Kavya","Keerthana","Lakshmi","Lavanya","Manasa","Meghana","Mounika","Nandini","Neha","Pallavi","Pooja","Priya","Ramya","Sahithi","Sanjana","Shreya","Sneha","Spandana","Sravani","Swathi","Tanvi","Vaishnavi","Varsha","Vidya"]
LAST_NAMES = ["Reddy","Sharma","Kumar","Naidu","Rao","Gupta","Patel","Singh","Chowdary","Varma","Prasad","Raju","Goud","Verma","Yadav","Patil","Agarwal","Das","Ghosh","Bhat"]

def seed():
    db = SessionLocal()
    try:
        print("=" * 50)
        print("SEEDING SECTION B - QUICK MODE")
        print("=" * 50)

        # Drop all and recreate
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("[1] Tables recreated")

        # ---- ADMIN ----
        admin = User(username="admin", email="admin@vibe.com", hashed_password=get_password_hash("admin123"), role=UserRole.ADMIN, is_active=True)
        db.add(admin)
        db.flush()
        print("[2] Admin created")

        # ---- SECTION ----
        sec_b = Section(name="Section B")
        db.add(sec_b)
        db.flush()
        print("[3] Section B created")

        # ---- SUBJECTS ----
        sub_map = {}
        for name, code, credits, stype in SEM6_SUBJECTS:
            st = SubjectType.NON_CREDIT if stype == "NON_CREDIT" else (SubjectType.LAB if stype == "LAB" else (SubjectType.NPTEL if stype == "NPTEL" else SubjectType.THEORY))
            s = Subject(name=name, code=code, semester=6, subject_type=st, credits=credits)
            db.add(s)
            sub_map[code] = s
        db.flush()

        # ---- HISTORICAL SUBJECTS (Sem 1-5) ----
        hist_sub_map = {}  # {sem_num: [Subject objects]}
        for sem_num, subj_list in HISTORICAL_SUBJECTS.items():
            hist_sub_map[sem_num] = []
            for name, code, credits, stype in subj_list:
                st = SubjectType.LAB if stype == "LAB" else SubjectType.THEORY
                s = Subject(name=name, code=code, semester=sem_num, subject_type=st, credits=credits)
                db.add(s)
                hist_sub_map[sem_num].append(s)
        db.flush()
        total_hist = sum(len(v) for v in hist_sub_map.values())
        print(f"[4] {len(sub_map)} sem-6 subjects + {total_hist} historical subjects created")

        # ---- FACULTY ----
        fac_map = {}  # emp_id -> Faculty
        mentor_id = None
        for fname, emp_id, uname, subj_list in FACULTY_B:
            is_coordinator = (emp_id == "1838")  # Niharika is class coordinator
            role = UserRole.BOTH if is_coordinator else UserRole.LECTURER
            u = User(username=uname, email=f"{uname}@griet.ac.in", hashed_password=get_password_hash("staff123"), role=role, is_active=True)
            db.add(u)
            db.flush()
            f = Faculty(user_id=u.id, employee_id=emp_id)
            db.add(f)
            db.flush()
            fac_map[emp_id] = f
            if is_coordinator:
                mentor_id = f.id
            # Faculty assignments
            for sub_code, _ in subj_list:
                if sub_code in sub_map:
                    db.add(FacultyAssignment(faculty_id=f.id, subject_id=sub_map[sub_code].id, section_id=sec_b.id))

        # Demo accounts
        mentor_u = User(username="mentor", email="mentor@vibe.com", hashed_password=get_password_hash("mentor123"), role=UserRole.MENTOR, is_active=True)
        db.add(mentor_u)
        db.flush()
        mentor_fac = Faculty(user_id=mentor_u.id, employee_id="FAC001")
        db.add(mentor_fac)
        db.flush()
        if not mentor_id:
            mentor_id = mentor_fac.id

        lect_u = User(username="lecturer", email="lecturer@vibe.com", hashed_password=get_password_hash("lecturer123"), role=UserRole.LECTURER, is_active=True)
        db.add(lect_u)
        db.flush()
        lect_fac = Faculty(user_id=lect_u.id, employee_id="FAC002")
        db.add(lect_fac)
        db.flush()
        # Link demo lecturer to ML Section B
        db.add(FacultyAssignment(faculty_id=lect_fac.id, subject_id=sub_map["GR22A3140"].id, section_id=sec_b.id))

        db.commit()
        print(f"[5] {len(fac_map)} faculty + 2 demo accounts created")

        # ---- 65 STUDENTS ----
        students = []
        risk_list = ["High"] * 10 + ["Medium"] * 15 + ["Low"] * 40
        random.shuffle(risk_list)

        for i in range(65):
            sid = f"23241A67{i+1:02d}"
            gender = random.choice(["M", "F"])
            first = random.choice(MALE_NAMES if gender == "M" else FEMALE_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            risk = risk_list[i]

            u = User(username=sid.lower(), email=f"{sid.lower()}@griet.ac.in", hashed_password=get_password_hash("student123"), role=UserRole.STUDENT, is_active=True)
            db.add(u)
            db.flush()
            s = Student(user_id=u.id, enrollment_number=sid, current_semester=6, mentor_id=mentor_id, section_id=sec_b.id)
            db.add(s)
            db.flush()

            if risk == "High":
                att_rate = random.uniform(0.45, 0.65)
                ability = random.uniform(0.30, 0.50)
            elif risk == "Medium":
                att_rate = random.uniform(0.70, 0.85)
                ability = random.uniform(0.55, 0.72)
            else:
                att_rate = random.uniform(0.85, 0.98)
                ability = random.uniform(0.78, 0.96)

            students.append((s, risk, att_rate, ability, name))

        # Demo student
        demo_u = User(username="student", email="student@vibe.com", hashed_password=get_password_hash("student123"), role=UserRole.STUDENT, is_active=True)
        db.add(demo_u)
        db.flush()
        demo_s = Student(user_id=demo_u.id, enrollment_number="23241A6700", current_semester=6, mentor_id=mentor_id, section_id=sec_b.id)
        db.add(demo_s)
        db.flush()
        students.append((demo_s, "Low", 0.90, 0.82, "Demo Student"))

        db.commit()
        print(f"[6] {len(students)} students created")

        # ---- HISTORICAL MARKS & ATTENDANCE (Sem 1-5) ----
        hist_marks_count = 0
        hist_att_count = 0
        for stu, risk, att_rate, ability, name in students:
            for sem_num, subj_list in hist_sub_map.items():
                # Vary ability slightly per semester for realistic trend
                sem_ability = ability + random.uniform(-0.05, 0.05)
                sem_ability = max(0.25, min(0.98, sem_ability))
                sem_att_rate = att_rate + random.uniform(-0.05, 0.05)
                sem_att_rate = max(0.35, min(0.99, sem_att_rate))

                for sub in subj_list:
                    sub_type = sub.subject_type.value if hasattr(sub.subject_type, 'value') else str(sub.subject_type)

                    if sub_type == "THEORY":
                        # Mid 1 marks (out of 30)
                        mid1_score = int(round(sem_ability * 30 + random.randint(-3, 3)))
                        mid1_score = max(5, min(30, mid1_score))
                        db.add(Marks(student_id=stu.id, subject_id=sub.id, assessment_type=AssessmentType.MID_1, score=mid1_score, total=30, label="Mid 1"))
                        # Mid 2 marks (out of 30)
                        mid2_score = int(round(sem_ability * 30 + random.randint(-3, 3)))
                        mid2_score = max(5, min(30, mid2_score))
                        db.add(Marks(student_id=stu.id, subject_id=sub.id, assessment_type=AssessmentType.MID_2, score=mid2_score, total=30, label="Mid 2"))
                        # End term marks (out of 100)
                        end_score = int(round(sem_ability * 100 + random.randint(-8, 8)))
                        end_score = max(15, min(100, end_score))
                        db.add(Marks(student_id=stu.id, subject_id=sub.id, assessment_type=AssessmentType.END_TERM, score=end_score, total=100, label="End Semester"))
                        hist_marks_count += 3
                    else:
                        # Lab internal (out of 40)
                        lab_score = int(round(sem_ability * 40 + random.randint(-3, 3)))
                        lab_score = max(10, min(40, lab_score))
                        db.add(Marks(student_id=stu.id, subject_id=sub.id, assessment_type=AssessmentType.LAB_INTERNAL, score=lab_score, total=40, label="Lab Internal"))
                        hist_marks_count += 1

                    # Generate 45 historical attendance records per subject
                    for day_offset in range(45):
                        present = random.random() < sem_att_rate
                        db.add(Attendance(student_id=stu.id, subject_id=sub.id, date=date(2025, 1, 1) + timedelta(days=day_offset), status=present))
                        hist_att_count += 1

        db.commit()
        print(f"[6b] Historical data: {hist_marks_count} marks + {hist_att_count} attendance records")


        # ---- ATTENDANCE (timetable-based) ----
        working_days = []
        cur = SEM_START
        while cur <= SIM_DATE:
            if not is_holiday(cur):
                dn = WEEKDAY_MAP.get(cur.weekday())
                if dn: working_days.append((cur, dn))
            cur += timedelta(days=1)

        att_count = 0
        for stu, risk, att_rate, ability, name in students:
            for day_date, day_name in working_days:
                for sub_code in get_subjects_for_day(day_name):
                    if sub_code not in sub_map: continue
                    present = random.random() < att_rate
                    db.add(Attendance(student_id=stu.id, subject_id=sub_map[sub_code].id, date=day_date, status=present))
                    att_count += 1

        db.commit()
        print(f"[7] {att_count} attendance records ({len(working_days)} working days)")

        # ---- MARKS (Mid-1 for theory, Lab internal) ----
        marks_count = 0
        for stu, risk, att_rate, ability, name in students:
            for sub_name, sub_code, credits, stype in SEM6_SUBJECTS:
                if sub_code not in sub_map: continue
                sub = sub_map[sub_code]

                if stype == "THEORY":
                    # Mid-1 (out of 30)
                    mid1 = round(max(3, min(29, 30 * ability + random.uniform(-5, 5))))
                    db.add(Marks(student_id=stu.id, subject_id=sub.id, assessment_type=AssessmentType.MID_1, score=mid1, total=30, label="Mid-1"))
                    # Assignment component (out of 5)
                    asn = round(max(0, min(5, 5 * att_rate + random.uniform(-1, 1))))
                    db.add(Marks(student_id=stu.id, subject_id=sub.id, assessment_type=AssessmentType.ASSIGNMENT, score=asn, total=5, label="Assignment Component"))
                    marks_count += 2
                elif stype == "LAB":
                    # Lab internal exam NOT yet conducted for current semester
                    pass
                elif stype == "NON_CREDIT":
                    # Non-credit treated as theory - has mid exams
                    mid1 = round(max(3, min(29, 30 * ability + random.uniform(-5, 5))))
                    db.add(Marks(student_id=stu.id, subject_id=sub.id, assessment_type=AssessmentType.MID_1, score=mid1, total=30, label="Mid-1"))
                    marks_count += 1
                # NPTEL: no internal marks (external exam only)

        db.commit()
        print(f"[8] {marks_count} marks records")

        # ---- FINALIZE MID-1 MARKS (prevent resubmission) ----
        fin_count = 0
        for sub_name, sub_code, credits, stype in SEM6_SUBJECTS:
            if sub_code not in sub_map: continue
            if stype in ("THEORY", "NON_CREDIT"):
                db.add(MarkFinalization(
                    subject_id=sub_map[sub_code].id,
                    section_id=sec_b.id,
                    assessment_type="mid_1",
                    is_finalized=True,
                    finalized_by=admin.id,
                    finalized_at=datetime(2026, 2, 25, 12, 0)
                ))
                fin_count += 1
            if stype == "LAB":
                db.add(MarkFinalization(
                    subject_id=sub_map[sub_code].id,
                    section_id=sec_b.id,
                    assessment_type="lab_internal",
                    is_finalized=True,
                    finalized_by=admin.id,
                    finalized_at=datetime(2026, 2, 25, 12, 0)
                ))
                fin_count += 1
        db.commit()
        print(f"[8b] {fin_count} mark finalizations (Mid-1 locked)")

        # ---- ASSIGNMENTS ----
        assign_data = [
            ("GR22A3140", "Assignment 1 - Linear Regression", "Implement linear regression from scratch.", "2026-01-25"),
            ("GR22A3140", "Assignment 2 - Decision Trees", "Build a decision tree classifier.", "2026-02-15"),
            ("GR22A3115", "Assignment 1 - DFA Construction", "Design DFA for given languages.", "2026-01-20"),
            ("GR22A3115", "Assignment 2 - CFG & PDA", "Convert CFG to PDA.", "2026-02-20"),
            ("GR22A3143", "Assignment 1 - Hadoop Setup", "Set up Hadoop and run WordCount.", "2026-01-28"),
            ("GR22A3143", "Assignment 2 - Hive Queries", "Write HiveQL queries.", "2026-02-25"),
            ("GR22A4048", "Assignment 1 - Classical Ciphers", "Implement Caesar and Vigenere.", "2026-01-22"),
            ("GR22A4048", "Assignment 2 - AES", "Implement AES encryption.", "2026-02-18"),
            ("NPTEL", "Assignment 1 - Python DS", "Solve problems on data structures.", "2026-01-30"),
        ]

        a_count = 0
        s_count = 0
        for sub_code, title, desc, due in assign_data:
            if sub_code not in sub_map: continue
            # Find faculty
            fac_id = lect_fac.id
            for _, eid, _, slist in FACULTY_B:
                if any(sc == sub_code for sc, _ in slist):
                    fac_id = fac_map[eid].id
                    break
            a = Assignment(title=title, description=desc, due_date=due, subject_id=sub_map[sub_code].id, section_id=sec_b.id, faculty_id=fac_id)
            db.add(a)
            db.flush()
            a_count += 1

            due_dt = datetime.strptime(due, "%Y-%m-%d").date()
            if due_dt < SIM_DATE:
                for stu, risk, att_rate, ability, name in students:
                    if random.random() < 0.85:
                        grade = random.randint(4, 10) if random.random() < 0.7 else None
                        db.add(Submission(assignment_id=a.id, student_id=stu.id, submission_date=due_dt - timedelta(days=random.randint(0, 2)), file_url=f"/uploads/{stu.enrollment_number}_{a.id}.pdf", grade=grade))
                        s_count += 1

        db.commit()
        print(f"[9] {a_count} assignments, {s_count} submissions")

        # ---- MATERIALS ----
        m_count = 0
        for sub_name, sub_code, _, stype in SEM6_SUBJECTS:
            if sub_code not in sub_map: continue
            fac_id = lect_fac.id
            for _, eid, _, slist in FACULTY_B:
                if any(sc == sub_code for sc, _ in slist):
                    fac_id = fac_map[eid].id
                    break
            db.add(Material(title=f"Course Notes - {sub_name}", description=f"Notes for {sub_name}", file_url=f"/uploads/{sub_code}_notes.pdf", subject_id=sub_map[sub_code].id, section_id=sec_b.id, faculty_id=fac_id))
            m_count += 1
        db.commit()
        print(f"[10] {m_count} materials")

        # ---- SYLLABUS TOPICS ----
        topics_data = {
            "GR22A3140": [("Introduction to ML", True), ("Regression & Classification", True), ("SVM & Ensemble Methods", False), ("Neural Networks", False), ("Clustering", False)],
            "GR22A3115": [("Finite Automata", True), ("Context-Free Grammars", True), ("Turing Machines", False), ("Lexical Analysis", False), ("Parsing", False)],
            "GR22A3143": [("Intro to Big Data", True), ("Hadoop Ecosystem", True), ("MapReduce", False), ("NoSQL", False), ("Spark", False)],
            "GR22A4048": [("Classical Encryption", True), ("Block Ciphers", True), ("Public Key Crypto", False), ("Hash Functions", False), ("Network Security", False)],
            "NPTEL": [("Python Basics", True), ("Control Flow", True), ("Data Structures", False), ("OOP", False), ("Libraries", False)],
            "GR22A2003": [("Preamble & Rights", True), ("Directive Principles", True), ("Government Structure", False)],
        }
        t_count = 0
        for sub_code, topics in topics_data.items():
            if sub_code not in sub_map: continue
            for order, (title, done) in enumerate(topics, 1):
                db.add(SyllabusTopic(title=title, subject_id=sub_map[sub_code].id, is_completed=done, order=order))
                t_count += 1
        db.commit()
        print(f"[11] {t_count} syllabus topics")

        # ---- ALERTS ----
        al_count = 0
        for stu, risk, att_rate, ability, name in students:
            if risk == "High":
                db.add(Alert(student_id=stu.id, message=f"HIGH risk. Attendance: {att_rate*100:.0f}%", type="High Risk"))
                al_count += 1
            elif risk == "Medium" and att_rate < 0.78:
                db.add(Alert(student_id=stu.id, message=f"Low attendance: {att_rate*100:.0f}%", type="Low Attendance"))
                al_count += 1
        db.commit()
        print(f"[12] {al_count} alerts")

        # ---- REMARKS ----
        r_count = 0
        for stu, risk, att_rate, ability, name in students:
            if risk == "High":
                msgs = ["Needs to improve attendance. Parents contacted.", "Academic performance discussed.", "Extra tutorials recommended."]
                db.add(Remark(student_id=stu.id, faculty_id=mentor_id, message=random.choice(msgs), created_at=datetime(2026, 3, random.randint(1, 20), 14, 0)))
                r_count += 1
        db.commit()
        print(f"[13] {r_count} remarks")

        # ---- DOUBTS ----
        d_count = 0
        doubt_data = [
            ("GR22A3140", "L1 vs L2 regularization?", "When to use Lasso vs Ridge?"),
            ("GR22A3115", "Pumping Lemma help", "How to use pumping lemma?"),
            ("GR22A3143", "MapReduce vs Spark", "Key differences?"),
            ("GR22A4048", "RSA key generation", "Step-by-step example?"),
        ]
        for sub_code, title, content in doubt_data:
            if sub_code not in sub_map: continue
            rand_stu = random.choice(students)[0]
            d = Doubt(title=title, content=content, student_id=rand_stu.id, subject_id=sub_map[sub_code].id, is_resolved=random.choice([True, False]), created_at=datetime(2026, 2, random.randint(1, 28), 10, 0))
            db.add(d)
            db.flush()
            d_count += 1
            if d.is_resolved:
                fac_uid = None
                for _, eid, _, slist in FACULTY_B:
                    if any(sc == sub_code for sc, _ in slist):
                        fac_uid = fac_map[eid].user_id
                        break
                if fac_uid:
                    db.add(DoubtComment(content="Great question! Here is the explanation...", doubt_id=d.id, user_id=fac_uid, created_at=d.created_at + timedelta(hours=5)))
        db.commit()
        print(f"[14] {d_count} doubts")

        # ---- QUIZZES ----
        q_count = 0
        qa_count = 0
        quiz_data = [
            ("GR22A3140", "ML Quiz 1", [
                ("Goal of supervised learning?", "Clustering", "Classification", "Reduction", "Selection", "b"),
                ("Gradient descent is used in?", "DT", "KNN", "Linear Reg", "NB", "c"),
                ("Overfitting means?", "Learns noise", "Too simple", "Generalizes", "Low bias", "a"),
            ]),
            ("GR22A3115", "ACD Quiz 1", [
                ("DFA stands for?", "Deterministic FA", "Dynamic FA", "Distributed FA", "Direct FA", "a"),
                ("NFA transitions?", "Only 1", "Multiple", "None", "Exactly 2", "b"),
                ("Pumping lemma disproves?", "CFL", "Regular", "Recursive", "CSL", "b"),
            ]),
        ]
        for sub_code, qtitle, questions in quiz_data:
            if sub_code not in sub_map: continue
            fac_uid = None
            for _, eid, _, slist in FACULTY_B:
                if any(sc == sub_code for sc, _ in slist):
                    fac_uid = fac_map[eid].user_id
                    break
            q = Quiz(title=qtitle, subject_id=sub_map[sub_code].id, section_id=sec_b.id, total_marks=len(questions), start_time=datetime(2026, 2, 1, 9, 0), end_time=datetime(2026, 2, 1, 9, 30), created_by=fac_uid)
            db.add(q)
            db.flush()
            q_count += 1

            qq_objs = []
            for qt, a, b, c, d_opt, correct in questions:
                qq = QuizQuestion(quiz_id=q.id, question_text=qt, option_a=a, option_b=b, option_c=c, option_d=d_opt, correct_option=correct, marks=1)
                db.add(qq)
                db.flush()
                qq_objs.append(qq)

            for stu, risk, att_rate, ability, name in students:
                if random.random() < 0.90:
                    score = 0
                    attempt = QuizAttempt(quiz_id=q.id, student_id=stu.id, marks_obtained=0, submitted_at=datetime(2026, 2, 1, 9, random.randint(10, 29)))
                    db.add(attempt)
                    db.flush()
                    for qqo in qq_objs:
                        if random.random() < ability:
                            sel = qqo.correct_option
                            score += 1
                        else:
                            sel = random.choice(["a", "b", "c", "d"])
                        db.add(QuizResponse(attempt_id=attempt.id, question_id=qqo.id, selected_option=sel))
                    attempt.marks_obtained = score
                    qa_count += 1

        db.commit()
        print(f"[15] {q_count} quizzes, {qa_count} attempts")

        # ---- DONE ----
        print("\n" + "=" * 50)
        print("[OK] DATABASE SEEDED - SECTION B")
        print("=" * 50)
        print("  admin    / admin123")
        print("  mentor   / mentor123")
        print("  lecturer / lecturer123")
        print("  student  / student123")
        print(f"  Faculty: {len(fac_map)} real + 2 demo")
        print(f"  Students: {len(students)}")
        print(f"  Attendance: {att_count}")
        print(f"  Marks: {marks_count}")
        print(f"  Assignments: {a_count}, Submissions: {s_count}")
        print("=" * 50)

    except Exception as e:
        import traceback
        log_path = os.path.join(current_dir, "seed_error.log")
        with open(log_path, "w", encoding="utf-8") as ef:
            ef.write(traceback.format_exc())
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        print(f"  Full traceback in: {log_path}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
