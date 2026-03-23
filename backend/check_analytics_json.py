
import sqlite3
import json

DB_PATH = "h:\\mini project\\vibe\\backend\\sql_app.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get a student from Section B
c.execute("SELECT id, enrollment_number FROM students WHERE enrollment_number = '23241A6701'")
student = c.fetchone()
student_id = student[0]

# Get subjects
c.execute("SELECT id, name, code, subject_type FROM subjects WHERE semester = 6")
subjects = c.fetchall()

result = []
for sub_id, name, code, stype in subjects:
    c.execute("SELECT assessment_type, score, total FROM marks WHERE student_id = ? AND subject_id = ?", (student_id, sub_id))
    marks = c.fetchall()
    
    sub_total_scored = sum(m[1] for m in marks)
    sub_total_max = sum(m[2] for m in marks)
    overall_marks_pct = round((sub_total_scored / sub_total_max) * 100, 1) if sub_total_max > 0 else 0
    
    result.append({
        "subject_name": name,
        "overall_marks_percentage": overall_marks_pct
    })

print(json.dumps(result, indent=2))
conn.close()
