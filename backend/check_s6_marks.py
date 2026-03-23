import sqlite3
import os

DB_PATH = "h:\\mini project\\vibe\\backend\\sql_app.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT id, enrollment_number FROM students WHERE enrollment_number = '23241A6701'")
student = c.fetchone()
print(f"Student: {student}")

c.execute("SELECT s.name, m.assessment_type, m.score, m.total FROM marks m JOIN subjects s ON s.id=m.subject_id WHERE s.semester=6 AND m.student_id=?", (student[0],))
marks = c.fetchall()
print(f"Sem 6 marks count: {len(marks)}")
for r in marks:
    print(r)

conn.close()
