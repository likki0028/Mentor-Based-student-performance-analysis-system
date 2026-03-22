import sqlite3, os
db_path = os.path.join(os.path.dirname(__file__), "sql_app.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, name, code, semester, subject_type, credits FROM subjects ORDER BY semester, id")
rows = c.fetchall()
with open("subject_report.txt", "w") as f:
    for r in rows:
        line = f"Sem {r[3]}: [{r[4]:6s}] {r[1]:50s} ({r[2]:12s}) {r[5]} cr"
        f.write(line + "\n")
    f.write(f"\nTotal: {len(rows)} subjects\n")

# Also check students
c.execute("SELECT id, enrollment_number, current_semester FROM students")
studs = c.fetchall()
with open("subject_report.txt", "a") as f:
    f.write(f"\nStudents ({len(studs)}):\n")
    for s in studs:
        f.write(f"  ID={s[0]}, Enrollment={s[1]}, CurrentSem={s[2]}\n")

conn.close()
print(f"Wrote {len(rows)} subjects and {len(studs)} students to subject_report.txt")
