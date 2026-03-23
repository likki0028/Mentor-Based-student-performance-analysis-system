"""
Re-populate 6th-semester marks because they were accidentally deleted.
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

# Get semester 6 subjects from DB
c.execute("SELECT id, code, name, semester, credits FROM subjects WHERE semester = 6 ORDER BY id")
s6_subjects = c.fetchall()

# Get all students
c.execute("SELECT id, enrollment_number FROM students")
all_students = c.fetchall()

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

marks_added = 0

for idx, (stu_id, enroll) in enumerate(all_students):
    s_data = cgpa_map.get(enroll)
    target_cgpa = s_data.get("cgpa", 7.0) if s_data else 7.0
    target_pct = target_cgpa * 10

    for sub_id, sub_code, sub_name, sub_sem, sub_credits in s6_subjects:
        is_lab = 'lab' in sub_name.lower()
        is_nptel = sub_name.lower() == 'joy of computing using python'
        is_non_credit = 'constitution' in sub_name.lower() or 'mini project' in sub_name.lower()
        
        subj_pct = clamp(target_pct + random.uniform(-8, 8), 5, 99)

        if is_lab:
            internal = int(round(clamp(subj_pct * 0.40, 0, 40)))
            c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                (stu_id, sub_id, "lab_internal", internal, 40, "Lab Internal"))
            marks_added += 1
        elif is_nptel:
            # NPTEL has no internal mid exams
            pass
        elif is_non_credit:
            mid1 = int(round(clamp(subj_pct * 0.40 + random.uniform(-3, 3), 0, 40)))
            c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                (stu_id, sub_id, "mid_1", mid1, 40, "Mid-1"))
            marks_added += 1
        else:
            mid1 = int(round(clamp(subj_pct * 0.30 + random.uniform(-3, 3), 0, 30)))
            asgn = int(round(clamp(subj_pct * 0.05, 0, 5)))
            c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                (stu_id, sub_id, "mid_1", mid1, 30, "Mid-1"))
            c.execute("INSERT INTO marks (student_id, subject_id, assessment_type, score, total, label) VALUES (?,?,?,?,?,?)",
                (stu_id, sub_id, "assignment", asgn, 5, "Assignment Component"))
            marks_added += 2

conn.commit()
conn.close()

print(f"Marks added: {marks_added}")
