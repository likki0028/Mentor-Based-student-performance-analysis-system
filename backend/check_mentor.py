import sqlite3
conn = sqlite3.connect('sql_app.db')
c = conn.cursor()

# All users with roles
c.execute("SELECT id, username, role FROM users ORDER BY id")
print("=== ALL USERS ===")
for row in c.fetchall():
    print(f"  User ID {row[0]}: {row[1]} ({row[2]})")

# All faculty with their user
c.execute("SELECT f.id, f.user_id, u.username, u.role FROM faculty f JOIN users u ON f.user_id = u.id ORDER BY f.id")
print("\n=== ALL FACULTY ===")
for row in c.fetchall():
    print(f"  Faculty ID {row[0]}: user_id={row[1]}, username={row[2]}, role={row[3]}")

# Student mentor assignments
c.execute("SELECT mentor_id, COUNT(*) FROM students GROUP BY mentor_id")
print("\n=== STUDENTS BY MENTOR ===")
for row in c.fetchall():
    print(f"  mentor_id={row[0]}: {row[1]} students")

conn.close()
