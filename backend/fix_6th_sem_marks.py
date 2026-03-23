"""
Recalculate actual backlog counts for all students based on
subjects < semester 6 with overall percentage < 40%
"""
import sqlite3

conn = sqlite3.connect('sql_app.db')
c = conn.cursor()

# Get all students' current semester
c.execute("SELECT id, enrollment_number, current_semester, backlogs FROM students")
students = c.fetchall()

updated = 0
for sid, enroll, current_sem, old_backlogs in students:
    current_sem = current_sem or 6
    # Count subjects from completed semesters where student scored < 40%
    c.execute("""
        SELECT COUNT(*) FROM (
            SELECT sub.id
            FROM marks m
            JOIN subjects sub ON sub.id = m.subject_id
            WHERE m.student_id = ? AND sub.semester < ?
            GROUP BY sub.id
            HAVING CAST(SUM(m.score) AS FLOAT) / NULLIF(SUM(m.total), 0) * 100 < 40
        )
    """, (sid, current_sem))
    actual_backlogs = c.fetchone()[0]
    
    if actual_backlogs != old_backlogs:
        c.execute("UPDATE students SET backlogs = ? WHERE id = ?", (actual_backlogs, sid))
        if old_backlogs > 0 or actual_backlogs > 0:
            print(f"  {enroll}: {old_backlogs} -> {actual_backlogs}")
        updated += 1

conn.commit()

# Verify
c.execute("SELECT enrollment_number, backlogs FROM students WHERE backlogs > 0 ORDER BY backlogs DESC")
with_backlogs = c.fetchall()
print(f"\n=== Students with actual backlogs (completed semesters only): {len(with_backlogs)} ===")
for r in with_backlogs:
    print(f"  {r[0]}: {r[1]} backlogs")

conn.close()
print(f"\nUpdated {updated} students. Done!")
