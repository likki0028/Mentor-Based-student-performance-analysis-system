import sqlite3
import os

db_path = 'backend/sql_app.db'
print(f"Checking database at: {os.path.abspath(db_path)}")

try:
    if not os.path.exists(db_path):
        print(f"ERROR: DB file not found at {db_path}")
        # Try finding it
        for root, dirs, files in os.walk('.'):
            if 'sql_app.db' in files:
                print(f"Found it at: {os.path.join(root, 'sql_app.db')}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables found: {[t[0] for t in tables]}")
    
    if ('push_subscriptions',) in tables:
        print("Table 'push_subscriptions' exists.")
        cursor.execute("PRAGMA table_info(push_subscriptions)")
        print("Schema for push_subscriptions:")
        for col in cursor.fetchall():
            print(col)
    else:
        print("CRITICAL: push_subscriptions table is MISSING!")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
