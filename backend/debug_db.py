import sys
import os
import sqlite3

connection = sqlite3.connect("h:/mini project/vibe/backend/sql_app.db")
cursor = connection.cursor()

print("--- USERS (student1 and admin) ---")
cursor.execute("SELECT id, username, role FROM users WHERE username IN ('student1', 'admin')")
users = cursor.fetchall()
for row in users:
    print(row)
    user_id = row[0]
    username = row[1]
    
    if username == 'student1':
        print(f"--- STUDENT PROFILE for {username} (user_id={user_id}) ---")
        cursor.execute(f"SELECT * FROM students WHERE user_id={user_id}")
        print(cursor.fetchall())

print("\n--- FACULTY COUNT ---")
cursor.execute("SELECT count(*) FROM faculty")
print(cursor.fetchall())

connection.close()
