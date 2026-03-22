
import sqlite3
import os

db_path = "sql_app.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Users Table ---")
    cursor.execute("SELECT id, username, role, is_active FROM users WHERE username LIKE 'mentor%'")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    print("\n--- Faculty Table ---")
    cursor.execute("SELECT f.id, f.user_id, u.username FROM faculty f JOIN users u ON f.user_id = u.id")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    conn.close()
