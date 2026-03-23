"""Check what data the analytics endpoint returns for semester_stats"""
import sqlite3

conn = sqlite3.connect('sql_app.db')
c = conn.cursor()

# Get a student's ID
c.execute("SELECT id, enrollment_number, current_semester FROM students LIMIT 1")
stu = c.fetchone()
print(f"Student: {stu[1]}, current_semester={stu[2]}")

# Check what marks exist by semester
c.execute("""
    SELECT sub.semester, COUNT(DISTINCT sub.id) as num_subjects, COUNT(*) as num_marks,
           SUM(m.score) as total_score, SUM(m.total) as total_max
    FROM marks m
    JOIN subjects sub ON sub.id = m.subject_id
    WHERE m.student_id = ?
    GROUP BY sub.semester
    ORDER BY sub.semester
""", (stu[0],))
print("\nMarks by semester:")
for r in c.fetchall():
    print(f"  Sem {r[0]}: {r[1]} subjects, {r[2]} marks records, score={r[3]}/{r[4]}")

# Check attendance by semester
c.execute("""
    SELECT sub.semester, COUNT(*) as total_classes, SUM(a.status) as attended
    FROM attendance a
    JOIN subjects sub ON sub.id = a.subject_id
    WHERE a.student_id = ?
    GROUP BY sub.semester
    ORDER BY sub.semester
""", (stu[0],))
print("\nAttendance by semester:")
for r in c.fetchall():
    print(f"  Sem {r[0]}: {r[2]}/{r[1]} classes attended")

# Check what semesters have subjects
c.execute("SELECT DISTINCT semester FROM subjects ORDER BY semester")
print(f"\nSemesters with subjects: {[r[0] for r in c.fetchall()]}")

conn.close()
