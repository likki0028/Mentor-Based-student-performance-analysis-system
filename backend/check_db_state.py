import sqlite3
conn = sqlite3.connect('sql_app.db')
c = conn.cursor()

c.execute("SELECT count(*) FROM subjects")
print("Subjects:", c.fetchone()[0])

c.execute("SELECT count(*) FROM students")
print("Students:", c.fetchone()[0])

c.execute("SELECT u.username FROM users u WHERE u.role = 'MENTOR'")
mentors = c.fetchall()
print("Mentors:", mentors)

c.execute("SELECT s.id, s.name FROM sections s")
secs = c.fetchall()
print("Sections:", secs)

c.execute("SELECT f.id, u.username FROM faculty f JOIN users u ON f.user_id = u.id")
facs = c.fetchall()
print("Faculty:", facs)

c.execute("SELECT count(*) FROM marks")
print("Marks:", c.fetchone()[0])

c.execute("SELECT count(*) FROM attendance")
print("Attendance:", c.fetchone()[0])

conn.close()
