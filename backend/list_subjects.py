import sqlite3
import os

db_path = "h:/mini project/vibe/backend/sql_app.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

print("--- SUBJECTS ---")
cursor.execute("SELECT id, name, code, semester FROM subjects")
subjects = cursor.fetchall()
for row in subjects:
    print(row)

connection.close()
