import sqlite3
c = sqlite3.connect('sql_app.db')
r = c.execute("SELECT id, name, subject_type FROM subjects WHERE code='GR22A2003'").fetchone()
if r:
    sub_id, name, stype = r
    print(f"Subject: {name} (ID: {sub_id}, Type: {stype})")
    
    marks = c.execute("SELECT id, assessment_type, score, total FROM marks WHERE student_id=1 AND subject_id=?", (sub_id,)).fetchall()
    print(f"Marks for Student 1: {marks}")
else:
    print("Subject GR22A2003 not found")
