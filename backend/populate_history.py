"""
Populate semesters 1-5 with marks and attendance.
Since DB subjects don't match JSON subjects, we generate marks
based on each student's target CGPA from the JSON data.
"""
import json, os, sqlite3, random
random.seed(42)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql_app.db")
JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "synthetic_students.json")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Load synthetic data for student CGPA targets
with open(JSON_PATH, "r", encoding="utf-8") as f:
    synthetic_students = json.load(f)
cgpa_map = {s["student_id"]: s for s in synthetic_students}

# Get semester 1-5 subjects from DB
c.execute("SELECT id, code, name, semester, credits FROM subjects WHERE semester < 6 ORDER BY semester, id")
past_subjects = c.fetchall()
print(f"Semester 1-5 subjects in DB: {len(past_subjects)}")
for s in past_subjects:
    print(f"  Sem {s[3]}: {s[1]} - {s[2]} (credits={s[4]})")

# Get all students
c.execute("SELECT id, enrollment_number, current_semester FROM students")
all_students = c.fetchall()
print(f"\nStudents: {len(all_students)}")

# Check what already exists
c.execute("SELECT COUNT(*) FROM marks m JOIN subjects s ON s.id=m.subject_id WHERE s.semester < 6")
existing = c.fetchone()[0]
print(f"Existing marks for sem 1-5: {existing}")

if existing > 0:
    print("Marks already exist for past semesters. Skipping.")
    conn.close()
    exit()

from datetime import date, timedelta

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

marks_added = 0
att_added = 0

# Group subjects by semester
from collections import defaultdict
sem_subjects = defaultdict(list)
for sub in past_subjects:
    sem_subjects[sub[3]].append(sub)  # sub = (id, code, name, semester, credits)

for idx, (stu_id, enroll, current_sem) in enumerate(all_students):
    # Get student's target CGPA from JSON
    s_data = cgpa_map.get(enroll)
    if not s_data:
        # For students not in JSON (like demo student), use middle CGPA
        target_cgpa = 7.0
        att_rate = 0.75
    else:
        target_cgpa = s_data.get("cgpa", 7.0)
        att_rate = s_data.get("overall_attendance_rate", 0.75)

    target_pct = target_cgpa * 10  # CGPA 7.5 -> ~75%

    for sem_num in range(1, 6):  # Semesters 1-5
        subjects = sem_subjects.get(sem_num, [])

        sem_dates = {
            1: date(2023, 7, 1), 2: date(2024, 1, 1), 3: date(2024, 7, 1),
            4: date(2025, 1, 1), 5: date(2025, 7, 1)
        }
        sem_start = sem_dates.get(sem_num, date(2024, 1, 1))

        for sub_id, sub_code, sub_name, sub_sem, sub_credits in subjects:
            is_lab = 'lab' in sub_name.lower()

            # Generate subject percentage around target +/- noise
            subj_pct = clamp(target_pct + random.uniform(-8, 8), 5, 99)

            if is_lab:
                # Lab: internal (40) + external (60)
                internal = int(round(clamp(subj_pct * 0.40, 0, 40)))
                external = int(round(clamp(subj_pct * 0.60, 0, 60)))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                    (stu_id, sub_id, "lab_internal", internal, 40, "Lab Internal"))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                    (stu_id, sub_id, "lab_external", external, 60, "Lab External"))
                marks_added += 2
            else:
                # Theory: mid_1 (30) + mid_2 (30) + end_term (60) + assignment (5)
                mid1 = int(round(clamp(subj_pct * 0.30 + random.uniform(-3, 3), 0, 30)))
                mid2 = int(round(clamp(subj_pct * 0.30 + random.uniform(-3, 3), 0, 30)))
                external = int(round(clamp(subj_pct * 0.60 + random.uniform(-3, 3), 0, 60)))
                asgn = int(round(clamp(subj_pct * 0.05, 0, 5)))

                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                    (stu_id, sub_id, "mid_1", mid1, 30, "Mid-1"))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                    (stu_id, sub_id, "mid_2", mid2, 30, "Mid-2"))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                    (stu_id, sub_id, "end_term", external, 60, "End Semester"))
                c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                    (stu_id, sub_id, "assignment", asgn, 5, "Assignment Component"))
                marks_added += 4

            # Generate attendance (~30 classes per subject per semester)
            num_classes = random.randint(28, 35)
            for day_i in range(num_classes):
                day_date = sem_start + timedelta(days=day_i * 3 + random.randint(0, 2))
                present = 1 if random.random() < att_rate else 0
                c.execute("INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?,?,?,?)",
                    (stu_id, sub_id, day_date.isoformat(), present))
                att_added += 1

    if (idx + 1) % 10 == 0:
        conn.commit()
        print(f"  Progress: {idx+1}/{len(all_students)} students... (marks: +{marks_added}, att: +{att_added})")

conn.commit()
conn.close()

print(f"\nDone!")
print(f"  Marks added: {marks_added}")
print(f"  Attendance added: {att_added}")
