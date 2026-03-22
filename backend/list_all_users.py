import sqlite3
import os

db_path = "h:/mini project/vibe/backend/sql_app.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

print("--- ALL USERS ---")
cursor.execute("SELECT id, username, role, is_active FROM users")
users = cursor.fetchall()
for row in users:
    print(row)

print("\n--- STUDENT PROFILES ---")
cursor.execute("SELECT user_id, enrollment_number FROM students")
print(cursor.fetchall())

print("\n--- FACULTY PROFILES ---")
cursor.execute("SELECT user_id, employee_id FROM faculty")
print(cursor.fetchall())

connection.close()
