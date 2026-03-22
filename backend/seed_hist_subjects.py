"""
Seed realistic subjects and marks/attendance for semesters 1-5.
"""
import sqlite3, os, random
from datetime import date, timedelta

random.seed(42)
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql_app.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get all students
c.execute("SELECT id FROM students")
student_ids = [row[0] for row in c.fetchall()]
print(f"Found {len(student_ids)} students")

# Subjects per semester (realistic CS curriculum)
SUBJECTS = {
    1: [
        ("Mathematics 1", "MATH101", "theory", 4),
        ("Physics", "PHY101", "theory", 4),
        ("English Communication", "ENG101", "theory", 3),
        ("Programming Fundamentals", "CS1A", "theory", 3),
        ("Programming Lab", "CS1L", "lab", 2),
        ("Engineering Drawing", "ME101", "theory", 2),
    ],
    2: [
        ("Mathematics 2", "MATH201", "theory", 4),
        ("Chemistry", "CHE201", "theory", 4),
        ("Digital Electronics", "EC201", "theory", 3),
        ("Data Structures", "CS201", "theory", 3),
        ("Data Structures Lab", "CS2L", "lab", 2),
        ("Environmental Science", "ES201", "theory", 2),
    ],
    3: [
        ("Discrete Mathematics", "MATH301", "theory", 4),
        ("Object Oriented Programming", "CS301", "theory", 4),
        ("Database Management Systems", "CS302", "theory", 3),
        ("OOP Lab", "CS3L1", "lab", 2),
        ("DBMS Lab", "CS3L2", "lab", 2),
        ("Soft Skills", "SS301", "theory", 2),
    ],
    4: [
        ("Operating Systems", "CS401", "theory", 4),
        ("Computer Networks", "CS402", "theory", 4),
        ("Design & Analysis of Algorithms", "CS403", "theory", 3),
        ("OS Lab", "CS4L1", "lab", 2),
        ("Networks Lab", "CS4L2", "lab", 2),
        ("Open Source Technologies", "OE401", "theory", 3),
    ],
    5: [
        ("Software Engineering", "CS501", "theory", 4),
        ("Web Technologies", "CS502", "theory", 3),
        ("Artificial Intelligence", "CS503", "theory", 4),
        ("Web Tech Lab", "CS5L1", "lab", 2),
        ("AI Lab", "CS5L2", "lab", 2),
        ("Professional Ethics", "HUM501", "theory", 2),
    ],
}

START_YEAR_MONTH = {1: (2022, 7), 2: (2023, 1), 3: (2023, 7), 4: (2024, 1), 5: (2024, 7)}

# Remove old placeholder subjects for semesters 1-5
for sem in range(1, 6):
    c.execute("SELECT id FROM subjects WHERE semester = ?", (sem,))
    old_ids = [r[0] for r in c.fetchall()]
    if old_ids:
        for sid in old_ids:
            c.execute("DELETE FROM marks WHERE subject_id = ?", (sid,))
            c.execute("DELETE FROM attendance WHERE subject_id = ?", (sid,))
        c.execute("DELETE FROM subjects WHERE semester = ?", (sem,))
        print(f"Removed {len(old_ids)} old subjects for Sem {sem}")

conn.commit()

# Insert new subjects and seed data
for sem, subject_list in SUBJECTS.items():
    yr, mo = START_YEAR_MONTH[sem]
    print(f"\nSeeding Sem {sem} ({yr}/{mo})...")

    for sub_name, sub_code, sub_type, credits in subject_list:
        c.execute(
            "INSERT INTO subjects (name, code, semester, credits, subject_type) VALUES (?, ?, ?, ?, ?)",
            (sub_name, sub_code, sem, credits, sub_type.upper())
        )
        sub_id = c.lastrowid

        for stud_id in student_ids:
            # Attendance: 35-50 classes
            total_classes = random.randint(35, 50)
            for day_offset in range(total_classes):
                att_date = date(yr, mo, 1) + timedelta(days=day_offset * 2)
                present = random.random() < random.uniform(0.65, 0.98)
                c.execute(
                    "INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?, ?, ?, ?)",
                    (stud_id, sub_id, att_date.isoformat(), int(present))
                )

            # Marks
            if sub_type == "theory":
                mid_score = random.randint(14, 38)
                end_term = random.randint(28, 58)
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'mid_term', ?, 40, 'Mid Term')", (stud_id, sub_id, mid_score))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'end_term', ?, 60, 'End Term')", (stud_id, sub_id, end_term))
            elif sub_type == "lab":
                lab_int = random.randint(22, 38)
                lab_ext = random.randint(32, 58)
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'internal', ?, 40, 'Lab Internal')", (stud_id, sub_id, lab_int))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?, ?, 'end_term', ?, 60, 'Lab External')", (stud_id, sub_id, lab_ext))

    conn.commit()
    print(f"  Sem {sem} done.")

# Summary
print("\n=== FINAL SUMMARY ===")
for sem in range(1, 7):
    c.execute("SELECT COUNT(*) FROM subjects WHERE semester = ?", (sem,))
    sub_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM marks m JOIN subjects s ON m.subject_id = s.id WHERE s.semester = ?", (sem,))
    marks_count = c.fetchone()[0]
    print(f"  Sem {sem}: {sub_count} subjects, {marks_count} marks")

conn.close()
print("\nDone!")
