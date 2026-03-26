"""
Seed ALL Data (v3) — 195 Students + Timetable-Based Attendance + Real Faculty
==============================================================================
Comprehensive seeding script that:
- Clears and repopulates the entire database
- Creates real faculty from the timetable images
- Creates 195 students (3 sections × 65) from synthetic_students.json
- Generates timetable-based attendance (per day, per subject, per section)
- Inserts marks (mid_1, assignments) for Sem 6 theory subjects
- Creates assignments, submissions, quizzes, doubts, materials, alerts, remarks
- Uses the CORRECTED section timetables (merged periods for labs)

Run:  python scripts/seed_all_data.py
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta, date

# Add the parent directory of 'backend' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    user, student, faculty, subject, section,
    attendance, marks, alert, assignment, submission, remark,
    material, syllabus_topic, doubt, doubt_comment,
    quiz, quiz_question, quiz_attempt, quiz_response,
    mark_finalization, assignment_file
)
from app.core.security import get_password_hash

# Import CURRICULUM from generate_synthetic_data
from scripts.generate_synthetic_data import CURRICULUM

random.seed(42)

# ============================================================================
# CORRECTED TIMETABLES (from images, with merged periods)
# ============================================================================
# Key: subject short code -> subject DB code
SHORT_TO_CODE = {
    "ML": "GR22A3140",
    "ACD": "GR22A3115",
    "BDA": "GR22A3143",
    "CNS": "GR22A4048",
    "NPTEL": "NPTEL",
    "ML LAB": "GR22A3142",
    "BDA LAB": "GR22A3148",
    "MP": "GR22A3089",
    "COI": "GR22A2003",
    "TRAINING": None,  # Skip training
}

# Timetables per section: day -> list of 7 periods (subject short codes)
# Periods: 1(9:00), 2(9:50), 3(10:40), 4(11:30), 5(12:55), 6(1:50), 7(2:40)
TIMETABLE = {
    "A": {
        "MON": ["COI", "BDA LAB", "BDA LAB", "BDA LAB", "ML", "ML", "NPTEL"],
        "TUE": [None, "ML", "ML", "ACD", "BDA", "CNS", "CNS"],
        "WED": ["ACD", "ACD", "CNS", "BDA", "ML LAB", "ML LAB", "ML LAB"],
        "THU": ["BDA", "BDA", "COI", "COI", "MP", "MP", "MP"],
        "FRI": ["TRAINING"] * 7,
        "SAT": ["CNS", "CNS", "ML", "BDA", "NPTEL", "NPTEL", "ACD"],
    },
    "B": {
        "MON": ["NPTEL", "ML LAB", "ML LAB", "ML LAB", "ACD", "ACD", "CNS"],
        "TUE": ["CNS", "MP", "MP", "MP", "BDA", "BDA", "NPTEL"],
        "WED": ["COI", "BDA LAB", "BDA LAB", "BDA LAB", "ML", "ML", "ML"],
        "THU": ["CNS", "BDA", "ML", "ML", "ACD", "COI", "COI"],
        "FRI": ["TRAINING"] * 7,
        "SAT": ["ACD", "ACD", "ACD", "BDA", "CNS", "CNS", "ML"],
    },
    "C": {
        "MON": ["ACD", "ACD", "CNS", "CNS", "BDA", "BDA", "NPTEL"],
        "TUE": ["BDA", "ML LAB", "ML LAB", "ML LAB", "ML", "ML", "CNS"],
        "WED": ["ML", "ML", "CNS", "CNS", "BDA", "NPTEL", "NPTEL"],
        "THU": ["COI", "COI", "ACD", "ACD", "BDA LAB", "BDA LAB", "BDA LAB"],
        "FRI": ["TRAINING"] * 7,
        "SAT": ["ML", "MP", "MP", "MP", "BDA", "ACD", "COI"],
    },
}

# Day name mapping for date.weekday() (0=Monday)
WEEKDAY_MAP = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"}

# ============================================================================
# FACULTY DATA (from timetable images)
# ============================================================================
FACULTY_RAW = [
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
    ("Ms. Y.P.S.S.V. Mohana", "1822", "mohana"),
    ("Ms. K. Kalpana", "1769", "kalpana"),
    ("Ms. S. Srilatha", "1837", "srilatha"),
    ("Mr. VSRK Raju", "1806", "vsrkraju"),
    ("Mr. K. Mallikarjuna Raju", "1726", "mallikarjuna"),
    ("Ms. Rashi Saxena", "1770", "rashisaxena"),
    ("Ms. D. S. Niharika", "1838", "niharika"),
]

# Faculty-Subject-Section assignments
FACULTY_ASSIGNMENTS = [
    # SEC A
    ("GR22A3140", "Section A", ["1741"]),       # ML
    ("GR22A3142", "Section A", ["1741", "1769"]),  # ML LAB
    ("GR22A3115", "Section A", ["1848"]),       # ACD
    ("GR22A3143", "Section A", ["1610"]),       # BDA
    ("GR22A3148", "Section A", ["1610", "1837"]),  # BDA LAB
    ("GR22A4048", "Section A", ["1695"]),       # CNS
    ("NPTEL", "Section A", ["1739"]),            # NPTEL
    ("GR22A3089", "Section A", ["1806", "1862"]),  # MP
    ("GR22A2003", "Section A", ["1836"]),       # COI

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

# Class Coordinators (mentors) — emp_id -> section letter
CLASS_COORDINATORS = {
    "1770": "A",  # Ms. Rashi Saxena
    "1838": "B",  # Ms. D. S. Niharika
    "1837": "C",  # Ms. S. Srilatha
}

# ============================================================================
# HOLIDAY / VACATION DATES
# ============================================================================
SEMESTER_START = date(2025, 12, 12)
SIMULATION_DATE = date(2026, 3, 21)

# Sankranti Vacation: 12-01-2026 to 17-01-2026
VACATION_START = date(2026, 1, 12)
VACATION_END = date(2026, 1, 17)

# Mid-1 Exams: 19-02-2026 to 21-02-2026 (no regular classes)
MID1_START = date(2026, 2, 19)
MID1_END = date(2026, 2, 21)

def is_holiday(d):
    """Check if a date is a holiday (no regular classes)."""
    # Sundays
    if d.weekday() == 6:
        return True
    # Sankranti Vacation
    if VACATION_START <= d <= VACATION_END:
        return True
    # Mid-1 Exams (separate schedule, not regular classes)
    if MID1_START <= d <= MID1_END:
        return True
    return False


def get_unique_subjects_for_day(section_letter, day_name):
    """Get unique subject codes scheduled on a given day for a section.
    Returns a set of subject codes (not short names), excluding TRAINING and None.
    For attendance, each unique subject gets ONE attendance record per day,
    regardless of how many periods it occupies.
    """
    if day_name not in TIMETABLE[section_letter]:
        return set()
    periods = TIMETABLE[section_letter][day_name]
    subjects = set()
    for short in periods:
        if short and short != "TRAINING":
            code = SHORT_TO_CODE.get(short)
            if code:
                subjects.add(code)
    return subjects


# ============================================================================
# QUIZ DATA
# ============================================================================
QUIZ_DATA = {
    "GR22A3140": [  # ML
        {
            "title": "ML Quiz 1 - Introduction & Regression",
            "questions": [
                ("What is the primary goal of supervised learning?", "Clustering", "Classification/Regression", "Dimensionality Reduction", "Feature Selection", "b"),
                ("Which algorithm uses the concept of 'gradient descent'?", "Decision Tree", "KNN", "Linear Regression", "Naive Bayes", "c"),
                ("What does 'overfitting' mean?", "Model learns noise", "Model is too simple", "Model generalizes well", "Model has low bias", "a"),
                ("Which metric is used for regression problems?", "Accuracy", "F1-Score", "RMSE", "AUC-ROC", "c"),
                ("What is the bias-variance tradeoff?", "Balancing model complexity", "Increasing data size", "Reducing features", "Adding layers", "a"),
            ]
        },
    ],
    "GR22A3115": [  # ACD
        {
            "title": "ACD Quiz 1 - Finite Automata",
            "questions": [
                ("What is a DFA?", "Deterministic FA", "Dynamic FA", "Distributed FA", "Direct FA", "a"),
                ("Which is NOT a component of FA?", "States", "Transitions", "Stack", "Alphabet", "c"),
                ("NFA can have how many transitions for one input?", "Only 1", "Multiple", "None", "Exactly 2", "b"),
                ("Regular expressions describe which languages?", "Context-free", "Regular", "Recursive", "Context-sensitive", "b"),
                ("Pumping lemma is used to?", "Prove regularity", "Disprove regularity", "Build DFA", "Minimize DFA", "b"),
            ]
        },
    ],
    "GR22A3143": [  # BDA
        {
            "title": "BDA Quiz 1 - Hadoop Basics",
            "questions": [
                ("What is HDFS?", "Hadoop Distributed File System", "High Data File System", "Hybrid Data Framework", "None", "a"),
                ("MapReduce has how many phases?", "1", "2", "3", "4", "b"),
                ("Which is the master node in HDFS?", "DataNode", "NameNode", "TaskTracker", "JobTracker", "b"),
                ("Default block size in HDFS?", "32MB", "64MB", "128MB", "256MB", "c"),
                ("YARN stands for?", "Yet Another Resource Negotiator", "Your Application Resource Node", "YARN Application Runner", "None", "a"),
            ]
        },
    ],
    "GR22A4048": [  # CNS
        {
            "title": "CNS Quiz 1 - Classical Encryption",
            "questions": [
                ("Caesar cipher is a type of?", "Substitution", "Transposition", "Block cipher", "Stream cipher", "a"),
                ("Key length in DES is?", "56 bits", "64 bits", "128 bits", "256 bits", "a"),
                ("AES stands for?", "Advanced Encryption Standard", "Applied Encryption System", "Automated Encryption Service", "None", "a"),
                ("RSA is based on?", "Discrete log", "Factoring large primes", "Elliptic curves", "Hash functions", "b"),
                ("Which is a symmetric cipher?", "RSA", "AES", "Diffie-Hellman", "ElGamal", "a"),
            ]
        },
    ],
    "NPTEL": [  # JCP
        {
            "title": "JCP Quiz 1 - Python Basics",
            "questions": [
                ("What type is 3.14 in Python?", "int", "float", "str", "complex", "b"),
                ("Which keyword is used for functions?", "func", "define", "def", "function", "c"),
                ("List is mutable in Python?", "True", "False", "Sometimes", "Depends", "a"),
                ("What does len() return?", "Type", "Length", "Index", "Value", "b"),
                ("Which is used for comments?", "//", "#", "/*", "--", "b"),
            ]
        },
    ],
}

# ============================================================================
# DOUBT DATA
# ============================================================================
DOUBT_DATA = {
    "GR22A3140": [
        ("Difference between L1 and L2 regularization?", "I understand both are used to prevent overfitting, but when should I use Lasso vs Ridge?"),
        ("Confusion about SVM kernel trick", "How does the kernel function map to higher dimensions without actually computing the transformation?"),
    ],
    "GR22A3115": [
        ("Pumping Lemma application", "Can someone explain with an example how to use pumping lemma to prove a language is not regular?"),
        ("NFA to DFA conversion steps", "I'm confused about the subset construction method. What happens with epsilon transitions?"),
    ],
    "GR22A3143": [
        ("MapReduce vs Spark", "What are the key differences and when should we prefer one over the other?"),
        ("HDFS replication factor", "Why is the default replication factor 3 and how does rack awareness work?"),
    ],
    "GR22A4048": [
        ("RSA key generation", "Can someone walk through the step-by-step process of generating RSA keys with a small example?"),
        ("Difference between MAC and Digital Signature", "Both provide authentication but what's the fundamental difference?"),
    ],
    "NPTEL": [
        ("List comprehension vs map()", "When should I use list comprehension vs the map function for transformations?"),
    ],
}

# ============================================================================
# ASSIGNMENT DATA
# ============================================================================
ASSIGNMENT_DATA = {
    "GR22A3140": [
        ("Assignment 1 - Linear Regression", "Implement linear regression from scratch using Python. Use gradient descent for optimization.", "2026-01-25"),
        ("Assignment 2 - Decision Trees", "Build a decision tree classifier for the Iris dataset. Calculate information gain manually.", "2026-02-15"),
        ("Assignment 3 - SVM & Kernels", "Compare SVM with different kernels (linear, RBF, polynomial) on a given dataset.", "2026-03-15"),
    ],
    "GR22A3115": [
        ("Assignment 1 - DFA Construction", "Design DFA for the language L = {w | w contains 'aba' as substring} over {a,b}.", "2026-01-20"),
        ("Assignment 2 - CFG & PDA", "Convert given CFG to PDA and trace acceptance of sample strings.", "2026-02-20"),
    ],
    "GR22A3143": [
        ("Assignment 1 - Hadoop Setup", "Set up a single-node Hadoop cluster and run a WordCount MapReduce job.", "2026-01-28"),
        ("Assignment 2 - Hive Queries", "Write HiveQL queries for the given e-commerce dataset. Include partitioning.", "2026-02-25"),
        ("Assignment 3 - Spark RDD", "Implement PageRank algorithm using Spark RDDs.", "2026-03-20"),
    ],
    "GR22A4048": [
        ("Assignment 1 - Classical Ciphers", "Implement Caesar, Playfair, and Vigenere ciphers in Python.", "2026-01-22"),
        ("Assignment 2 - AES Implementation", "Implement AES encryption/decryption for a given plaintext.", "2026-02-18"),
    ],
    "NPTEL": [
        ("Assignment 1 - Python Data Structures", "Solve 10 problems on lists, tuples, dictionaries and sets.", "2026-01-30"),
        ("Assignment 2 - File Handling & OOP", "Build a student management system using classes and file I/O.", "2026-02-28"),
    ],
    "GR22A3142": [  # ML Lab
        ("Lab 1 - Data Preprocessing", "Clean and preprocess the Titanic dataset. Handle missing values and encode features.", "2026-01-25"),
        ("Lab 2 - Classification Models", "Implement and compare KNN, Naive Bayes, and Logistic Regression.", "2026-02-22"),
    ],
    "GR22A3148": [  # BDA Lab
        ("Lab 1 - HDFS Operations", "Perform basic HDFS file operations: put, get, ls, cat, mkdir.", "2026-01-27"),
        ("Lab 2 - MapReduce Programming", "Write a MapReduce program to find the average temperature per year.", "2026-02-24"),
    ],
    "GR22A3089": [  # Mini Project
        ("Mini Project Proposal", "Submit a 2-page proposal for your mini project including problem statement and methodology.", "2026-01-15"),
        ("Mini Project Progress Report", "Submit mid-semester progress report with initial implementation screenshots.", "2026-03-01"),
    ],
}

# ============================================================================
# SYLLABUS TOPICS
# ============================================================================
SYLLABUS_TOPICS = {
    "GR22A3140": [  # ML
        ("Unit 1: Introduction to ML", True),
        ("Unit 2: Regression & Classification", True),
        ("Unit 3: SVM & Ensemble Methods", False),  # In progress
        ("Unit 4: Neural Networks", False),
        ("Unit 5: Clustering & Dimensionality Reduction", False),
    ],
    "GR22A3115": [  # ACD
        ("Unit 1: Finite Automata & Regular Expressions", True),
        ("Unit 2: Context-Free Grammars & PDA", True),
        ("Unit 3: Turing Machines", False),
        ("Unit 4: Compiler Design - Lexical Analysis", False),
        ("Unit 5: Compiler Design - Parsing", False),
    ],
    "GR22A3143": [  # BDA
        ("Unit 1: Introduction to Big Data", True),
        ("Unit 2: Hadoop Ecosystem", True),
        ("Unit 3: MapReduce Programming", False),
        ("Unit 4: NoSQL Databases", False),
        ("Unit 5: Spark & Stream Processing", False),
    ],
    "GR22A4048": [  # CNS
        ("Unit 1: Classical Encryption Techniques", True),
        ("Unit 2: Block & Stream Ciphers", True),
        ("Unit 3: Public Key Cryptography", False),
        ("Unit 4: Authentication & Hash Functions", False),
        ("Unit 5: Network Security", False),
    ],
    "NPTEL": [  # JCP
        ("Unit 1: Python Basics & Data Types", True),
        ("Unit 2: Control Flow & Functions", True),
        ("Unit 3: Data Structures & File Handling", False),
        ("Unit 4: OOP in Python", False),
        ("Unit 5: Libraries & Applications", False),
    ],
    "GR22A2003": [  # COI
        ("Unit 1: Preamble & Fundamental Rights", True),
        ("Unit 2: Directive Principles & Duties", True),
        ("Unit 3: Union & State Government", False),
    ],
}


# ============================================================================
# MAIN SEED FUNCTION
# ============================================================================
def seed_all():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("SEED ALL DATA v3 — Comprehensive Population")
        print("=" * 60)

        Base.metadata.create_all(bind=engine)

        # =========================================================
        # STEP 1: Clear ALL existing data (Postgres Safe)
        # =========================================================
        print("\n[1/12] Clearing existing data...")
        if "postgresql" in str(engine.url):
             from sqlalchemy import text
             with engine.connect() as conn:
                 conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
                 conn.commit()
             print("  Postgres Schema cleared via CASCADE!")
        else:
            # Fallback for SQLite
            Base.metadata.drop_all(bind=engine)
            
        Base.metadata.create_all(bind=engine)
        print("  Done!")

        # =========================================================
        # STEP 2: Create Admin
        # =========================================================
        print("\n[2/12] Creating Admin...")
        admin_user = user.User(
            username="admin", email="admin@vibe.com",
            hashed_password=get_password_hash("admin123"),
            role=user.UserRole.ADMIN, is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("  Admin created (admin / admin123)")

        # =========================================================
        # STEP 3: Create Sections
        # =========================================================
        print("\n[3/12] Creating Sections...")
        db_sections = {}
        for sec_name in ["A", "B", "C"]:
            sec = section.Section(name=f"Section {sec_name}")
            db.add(sec)
            db_sections[sec_name] = sec
        db.commit()
        print(f"  Created 3 sections")

        # =========================================================
        # STEP 4: Create ALL Subjects (Sem 1-6)
        # =========================================================
        print("\n[4/12] Creating Subjects...")
        from app.models.subject import SubjectType
        db_subjects = {}
        for sem_num, sem_info in CURRICULUM.items():
            for subj in sem_info["subjects"]:
                stype = subj["type"].lower()
                if stype == "non-credit":
                    final_type = SubjectType.NON_CREDIT
                elif stype == "lab":
                    final_type = SubjectType.LAB
                else:
                    final_type = SubjectType.THEORY

                sub = subject.Subject(
                    name=subj["name"], code=subj["code"],
                    semester=sem_num, subject_type=final_type,
                    credits=subj["credits"]
                )
                db.add(sub)
                db_subjects[subj["code"]] = sub
        db.commit()
        print(f"  Created {len(db_subjects)} subjects across 6 semesters")

        # =========================================================
        # STEP 5: Create Faculty (Real from timetable)
        # =========================================================
        print("\n[5/12] Creating Faculty...")
        faculty_map = {}  # emp_id -> Faculty obj
        mentor_map = {}   # section_letter -> Faculty.id

        for name, emp_id, uname in FACULTY_RAW:
            # Determine role: if class coordinator -> BOTH (mentor + lecturer)
            is_coordinator = emp_id in CLASS_COORDINATORS
            role = user.UserRole.BOTH if is_coordinator else user.UserRole.LECTURER

            u = user.User(
                username=uname,
                email=f"{uname}@griet.ac.in",
                hashed_password=get_password_hash("staff123"),
                role=role, is_active=True
            )
            db.add(u)
            db.flush()

            f = faculty.Faculty(user_id=u.id, employee_id=emp_id)
            db.add(f)
            db.flush()
            faculty_map[emp_id] = f

            if is_coordinator:
                sec_letter = CLASS_COORDINATORS[emp_id]
                mentor_map[sec_letter] = f.id
                print(f"  Mentor for Section {sec_letter}: {name} ({uname})")

        # Also create generic demo accounts for easy testing
        # demo mentor
        demo_mentor_user = user.User(
            username="mentor", email="mentor@vibe.com",
            hashed_password=get_password_hash("mentor123"),
            role=user.UserRole.MENTOR, is_active=True
        )
        db.add(demo_mentor_user)
        db.flush()
        demo_mentor_fac = faculty.Faculty(user_id=demo_mentor_user.id, employee_id="FAC001")
        db.add(demo_mentor_fac)
        db.flush()

        # demo lecturer
        demo_lect_user = user.User(
            username="lecturer", email="lecturer@vibe.com",
            hashed_password=get_password_hash("lecturer123"),
            role=user.UserRole.LECTURER, is_active=True
        )
        db.add(demo_lect_user)
        db.flush()
        demo_lect_fac = faculty.Faculty(user_id=demo_lect_user.id, employee_id="FAC002")
        db.add(demo_lect_fac)
        db.flush()

        db.commit()
        print(f"  Created {len(faculty_map)} real faculty + 2 demo accounts")

        # =========================================================
        # STEP 6: Create Faculty-Subject-Section Assignments
        # =========================================================
        print("\n[6/12] Creating Faculty Assignments...")
        fa_count = 0
        for sub_code, sec_name, emp_ids in FACULTY_ASSIGNMENTS:
            if sub_code not in db_subjects:
                continue
            sub = db_subjects[sub_code]
            sec_letter = sec_name.split()[-1]  # "Section A" -> "A"
            sec = db_sections[sec_letter]
            for eid in emp_ids:
                f = faculty_map[eid]
                db.add(faculty.FacultyAssignment(
                    faculty_id=f.id, subject_id=sub.id, section_id=sec.id
                ))
                fa_count += 1

        # Also link demo lecturer to Section A ML for testing
        if "GR22A3140" in db_subjects:
            db.add(faculty.FacultyAssignment(
                faculty_id=demo_lect_fac.id,
                subject_id=db_subjects["GR22A3140"].id,
                section_id=db_sections["A"].id
            ))

        db.commit()
        print(f"  Created {fa_count} faculty-subject-section assignments")

        # =========================================================
        # STEP 7: Create Students from synthetic_students.json
        # =========================================================
        print("\n[7/12] Creating 195 Students...")
        json_path = os.path.join(current_dir, "synthetic_students.json")
        with open(json_path, "r", encoding="utf-8") as f_json:
            synthetic_students = json.load(f_json)

        db_students = []  # list of (Student obj, synthetic data dict)
        for idx, s_data in enumerate(synthetic_students):
            student_id_str = s_data["student_id"]
            sec_letter = s_data["section"]
            username = student_id_str.lower()

            s_user = user.User(
                username=username,
                email=f"{username}@griet.ac.in",
                hashed_password=get_password_hash("student123"),
                role=user.UserRole.STUDENT, is_active=True
            )
            db.add(s_user)
            db.flush()

            stu = student.Student(
                user_id=s_user.id,
                enrollment_number=student_id_str,
                current_semester=6,
                mentor_id=mentor_map.get(sec_letter, demo_mentor_fac.id),
                section_id=db_sections[sec_letter].id
            )
            db.add(stu)
            db_students.append((stu, s_data))

        # Known demo student login
        student_user = user.User(
            username="student", email="student@vibe.com",
            hashed_password=get_password_hash("student123"),
            role=user.UserRole.STUDENT, is_active=True
        )
        db.add(student_user)
        db.flush()
        demo_stu = student.Student(
            user_id=student_user.id,
            enrollment_number="23241A6700",
            current_semester=6,
            mentor_id=mentor_map.get("A", demo_mentor_fac.id),
            section_id=db_sections["A"].id
        )
        db.add(demo_stu)
        db.commit()
        print(f"  Created {len(db_students)} students + 1 demo (student / student123)")

        # =========================================================
        # STEP 8: Insert Marks (Past Semesters + Current Sem 6)
        # =========================================================
        print("\n[8/12] Inserting Marks...")
        marks_count = 0
        for stu_obj, s_data in db_students:
            db.flush()
            for sem in s_data["semesters"]:
                sem_num = sem["semester"]
                for subj_data in sem["subjects"]:
                    subj_code = subj_data["code"]
                    if subj_code not in db_subjects:
                        continue
                    sub_obj = db_subjects[subj_code]
                    db.flush()
                    m = subj_data["marks"]

                    if subj_data["type"] == "Theory":
                        # Mid 1
                        db.add(marks.Marks(
                            student_id=stu_obj.id, subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.MID_1,
                            score=m["mid1_total"], total=30,
                            label="Mid-1"
                        ))
                        marks_count += 1

                        # For completed semesters, add mid2 and external
                        if sem_num < 6:
                            db.add(marks.Marks(
                                student_id=stu_obj.id, subject_id=sub_obj.id,
                                assessment_type=marks.AssessmentType.MID_2,
                                score=m["mid2_total"], total=30,
                                label="Mid-2"
                            ))
                            db.add(marks.Marks(
                                student_id=stu_obj.id, subject_id=sub_obj.id,
                                assessment_type=marks.AssessmentType.END_TERM,
                                score=m["external"], total=60,
                                label="End Semester"
                            ))
                            marks_count += 2

                        # Assignment marks (out of 5)
                        db.add(marks.Marks(
                            student_id=stu_obj.id, subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.ASSIGNMENT,
                            score=m["internal_assignments"], total=5,
                            label="Assignment Component"
                        ))
                        marks_count += 1

                    elif subj_data["type"] == "Lab":
                        db.add(marks.Marks(
                            student_id=stu_obj.id, subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.LAB_INTERNAL,
                            score=m["internal_total"], total=40,
                            label="Lab Internal"
                        ))
                        marks_count += 1
                        if sem_num < 6:
                            db.add(marks.Marks(
                                student_id=stu_obj.id, subject_id=sub_obj.id,
                                assessment_type=marks.AssessmentType.LAB_EXTERNAL,
                                score=m["external"], total=60,
                                label="Lab External"
                            ))
                            marks_count += 1

                    else:  # Non-Credit
                        db.add(marks.Marks(
                            student_id=stu_obj.id, subject_id=sub_obj.id,
                            assessment_type=marks.AssessmentType.MID_1,
                            score=m["mid1"], total=40,
                            label="Mid-1"
                        ))
                        marks_count += 1

            # Commit every 20 students
            if (db_students.index((stu_obj, s_data)) + 1) % 20 == 0:
                db.commit()
                done = db_students.index((stu_obj, s_data)) + 1
                print(f"    Marks progress: {done}/{len(db_students)} students...")

        db.commit()
        print(f"  Done! {marks_count} marks records")

        # =========================================================
        # STEP 9: Generate TIMETABLE-BASED Attendance (Sem 6 only)
        # =========================================================
        print("\n[9/12] Generating timetable-based attendance...")
        attendance_count = 0
        current = SEMESTER_START

        # Pre-compute working days and their subjects per section
        working_days = []
        while current <= SIMULATION_DATE:
            if not is_holiday(current):
                day_name = WEEKDAY_MAP[current.weekday()]
                if day_name != "SUN":
                    working_days.append((current, day_name))
            current += timedelta(days=1)

        print(f"  Working days: {len(working_days)} (from {SEMESTER_START} to {SIMULATION_DATE})")

        for stu_obj, s_data in db_students:
            db.flush()
            sec_letter = s_data["section"]
            att_rate = s_data["overall_attendance_rate"]

            for day_date, day_name in working_days:
                subjects_today = get_unique_subjects_for_day(sec_letter, day_name)
                for sub_code in subjects_today:
                    if sub_code not in db_subjects:
                        continue
                    sub_obj = db_subjects[sub_code]

                    # Determine attendance with student's individual rate + random noise
                    present = random.random() < att_rate
                    db.add(attendance.Attendance(
                        student_id=stu_obj.id,
                        subject_id=sub_obj.id,
                        date=day_date,
                        status=present
                    ))
                    attendance_count += 1

            # Commit every 20 students
            idx = db_students.index((stu_obj, s_data))
            if (idx + 1) % 20 == 0:
                db.commit()
                print(f"    Attendance progress: {idx+1}/{len(db_students)} students...")

        db.commit()
        print(f"  Done! {attendance_count} attendance records")

        # =========================================================
        # STEP 10: Create Assignments, Submissions, Materials, Syllabus
        # =========================================================
        print("\n[10/12] Creating Assignments, Materials, Syllabus Topics...")
        assign_count = 0
        sub_count = 0
        mat_count = 0
        topic_count = 0

        for sub_code, assignments_list in ASSIGNMENT_DATA.items():
            if sub_code not in db_subjects:
                continue
            sub_obj = db_subjects[sub_code]

            for sec_letter, sec_obj in db_sections.items():
                # Find the faculty for this subject-section
                fac_id = None
                for sc, sn, eids in FACULTY_ASSIGNMENTS:
                    if sc == sub_code and sn == f"Section {sec_letter}":
                        fac_id = faculty_map[eids[0]].id
                        break
                if not fac_id:
                    fac_id = demo_lect_fac.id

                for title, desc, due_str in assignments_list:
                    a = assignment.Assignment(
                        title=title, description=desc,
                        due_date=due_str,
                        subject_id=sub_obj.id,
                        section_id=sec_obj.id,
                        faculty_id=fac_id
                    )
                    db.add(a)
                    db.flush()
                    assign_count += 1

                    # Create submissions for past-due assignments
                    due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                    if due_date < SIMULATION_DATE:
                        section_students = [(s, d) for s, d in db_students if d["section"] == sec_letter]
                        for stu_obj, s_data in section_students:
                            # ~85% submission rate
                            if random.random() < 0.85:
                                sub_date = due_date - timedelta(days=random.randint(0, 3))
                                grade = random.randint(3, 10) if random.random() < 0.7 else None
                                db.add(submission.Submission(
                                    assignment_id=a.id,
                                    student_id=stu_obj.id,
                                    submission_date=sub_date,
                                    file_url=f"/uploads/submissions/{stu_obj.enrollment_number}_{a.id}.pdf",
                                    grade=grade
                                ))
                                sub_count += 1

                # Create 1 material per subject-section
                db.add(material.Material(
                    title=f"Course Notes - {sub_obj.name}",
                    description=f"Comprehensive notes for {sub_obj.name}",
                    file_url=f"/uploads/materials/{sub_code}_notes.pdf",
                    subject_id=sub_obj.id,
                    section_id=sec_obj.id,
                    faculty_id=fac_id
                ))
                mat_count += 1

        # Syllabus Topics (shared across sections, only one per subject)
        for sub_code, topics in SYLLABUS_TOPICS.items():
            if sub_code not in db_subjects:
                continue
            sub_obj = db_subjects[sub_code]
            for order, (title, completed) in enumerate(topics, 1):
                db.add(syllabus_topic.SyllabusTopic(
                    title=title,
                    subject_id=sub_obj.id,
                    is_completed=completed,
                    order=order
                ))
                topic_count += 1

        db.commit()
        print(f"  Assignments: {assign_count}, Submissions: {sub_count}")
        print(f"  Materials: {mat_count}, Syllabus Topics: {topic_count}")

        # =========================================================
        # STEP 11: Create Quizzes, Questions, Attempts, Responses
        # =========================================================
        print("\n[11/12] Creating Quizzes...")
        quiz_count = 0
        attempt_count = 0

        for sub_code, quizzes in QUIZ_DATA.items():
            if sub_code not in db_subjects:
                continue
            sub_obj = db_subjects[sub_code]

            for q_data in quizzes:
                for sec_letter, sec_obj in db_sections.items():
                    # Find faculty
                    fac_user_id = None
                    for sc, sn, eids in FACULTY_ASSIGNMENTS:
                        if sc == sub_code and sn == f"Section {sec_letter}":
                            fac_user_id = faculty_map[eids[0]].user_id
                            break

                    q = quiz.Quiz(
                        title=q_data["title"],
                        subject_id=sub_obj.id,
                        section_id=sec_obj.id,
                        total_marks=len(q_data["questions"]),
                        start_time=datetime(2026, 2, 1, 9, 0),
                        end_time=datetime(2026, 2, 1, 9, 30),
                        created_by=fac_user_id
                    )
                    db.add(q)
                    db.flush()
                    quiz_count += 1

                    # Add questions
                    q_objs = []
                    for qtext, oa, ob, oc, od, correct in q_data["questions"]:
                        qq = quiz_question.QuizQuestion(
                            quiz_id=q.id,
                            question_text=qtext,
                            option_a=oa, option_b=ob, option_c=oc, option_d=od,
                            correct_option=correct, marks=1
                        )
                        db.add(qq)
                        db.flush()
                        q_objs.append(qq)

                    # Create attempts for section students
                    section_students = [(s, d) for s, d in db_students if d["section"] == sec_letter]
                    for stu_obj, s_data in section_students:
                        # ~90% attempt rate
                        if random.random() < 0.90:
                            total_score = 0
                            attempt = quiz_attempt.QuizAttempt(
                                quiz_id=q.id,
                                student_id=stu_obj.id,
                                marks_obtained=0,
                                submitted_at=datetime(2026, 2, 1, 9, random.randint(10, 29))
                            )
                            db.add(attempt)
                            db.flush()

                            for qq_obj in q_objs:
                                # Student answer based on ability
                                ability = s_data["overall_attendance_rate"]
                                if random.random() < ability:
                                    sel = qq_obj.correct_option
                                    total_score += 1
                                else:
                                    sel = random.choice(["a", "b", "c", "d"])

                                db.add(quiz_response.QuizResponse(
                                    attempt_id=attempt.id,
                                    question_id=qq_obj.id,
                                    selected_option=sel
                                ))

                            attempt.marks_obtained = total_score
                            attempt_count += 1

        db.commit()
        print(f"  Quizzes: {quiz_count}, Attempts: {attempt_count}")

        # =========================================================
        # STEP 12: Doubts, Alerts, Remarks
        # =========================================================
        print("\n[12/12] Creating Doubts, Alerts, Remarks...")
        doubt_count = 0
        alert_count = 0
        remark_count = 0

        # Doubts
        for sub_code, doubts_list in DOUBT_DATA.items():
            if sub_code not in db_subjects:
                continue
            sub_obj = db_subjects[sub_code]

            for title, content in doubts_list:
                for sec_letter in ["A", "B", "C"]:
                    section_students = [(s, d) for s, d in db_students if d["section"] == sec_letter]
                    if not section_students:
                        continue
                    random_stu = random.choice(section_students)[0]
                    db.flush()

                    d = doubt.Doubt(
                        title=title,
                        content=content,
                        student_id=random_stu.id,
                        subject_id=sub_obj.id,
                        is_resolved=random.choice([True, False]),
                        created_at=datetime(2026, random.randint(1, 3), random.randint(1, 28), 10, 0)
                    )
                    db.add(d)
                    db.flush()
                    doubt_count += 1

                    # Add a faculty reply for resolved doubts
                    if d.is_resolved:
                        # find faculty for this subject-section
                        fac_user_id = None
                        for sc, sn, eids in FACULTY_ASSIGNMENTS:
                            if sc == sub_code and sn == f"Section {sec_letter}":
                                fac_user_id = faculty_map[eids[0]].user_id
                                break
                        if fac_user_id:
                            db.add(doubt_comment.DoubtComment(
                                content="Good question! Here's the explanation...",
                                doubt_id=d.id,
                                user_id=fac_user_id,
                                created_at=d.created_at + timedelta(hours=random.randint(2, 48))
                            ))

        # Alerts
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
                    message=f"Low attendance warning. Current: {att_rate*100:.1f}%",
                    type="Low Attendance"
                ))
                alert_count += 1

        # Remarks from mentors for high-risk students
        for stu_obj, s_data in db_students:
            if s_data["risk_profile"] == "High":
                sec_letter = s_data["section"]
                mentor_id = mentor_map.get(sec_letter)
                if mentor_id:
                    remarks_options = [
                        "Student needs to improve attendance urgently. Called parents.",
                        "Discussed academic performance. Student promised to attend regularly.",
                        "Low attendance and marks. Recommended extra tutorials.",
                        "Parent-teacher meeting scheduled regarding academic performance.",
                    ]
                    db.add(remark.Remark(
                        student_id=stu_obj.id,
                        faculty_id=mentor_id,
                        message=random.choice(remarks_options),
                        created_at=datetime(2026, 3, random.randint(1, 20), 14, 0)
                    ))
                    remark_count += 1

        db.commit()
        print(f"  Doubts: {doubt_count}, Alerts: {alert_count}, Remarks: {remark_count}")

        # =========================================================
        # SUMMARY
        # =========================================================
        print(f"\n{'=' * 60}")
        print("[OK] DATABASE SEEDED SUCCESSFULLY!")
        print(f"{'=' * 60}")
        print(f"  Admin:       admin / admin123")
        print(f"  Mentor:      mentor / mentor123")
        print(f"  Lecturer:    lecturer / lecturer123")
        print(f"  Real Faculty: {len(FACULTY_RAW)} (password: staff123)")
        print(f"  Students:    {len(db_students)} (student / student123 for demo)")
        print(f"  Sections:    3")
        print(f"  Subjects:    {len(db_subjects)}")
        print(f"  Marks:       {marks_count}")
        print(f"  Attendance:  {attendance_count}")
        print(f"  Assignments: {assign_count}")
        print(f"  Submissions: {sub_count}")
        print(f"  Quizzes:     {quiz_count}")
        print(f"  Quiz Attempts: {attempt_count}")
        print(f"  Doubts:      {doubt_count}")
        print(f"  Alerts:      {alert_count}")
        print(f"  Remarks:     {remark_count}")
        print(f"  Materials:   {mat_count}")
        print(f"  Syllabus:    {topic_count}")
        print(f"{'=' * 60}")

    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        log_path = os.path.join(current_dir, "seed_error.log")
        with open(log_path, "w", encoding="utf-8") as err_f:
            err_f.write(err_msg)
        print(f"\n[ERROR] Error seeding data (see seed_error.log): {type(e).__name__}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
