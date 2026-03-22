
import sqlite3
import os

db_path = 'sql_app.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, role FROM users WHERE role IN ('lecturer', 'mentor', 'both')")
        users = cursor.fetchall()
        print("Lecturer/Mentor Users:", users)
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()
