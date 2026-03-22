from app.core.security import verify_password, get_password_hash
import sqlite3
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

db_path = "h:/mini project/vibe/backend/sql_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT username, hashed_password FROM users WHERE username='admin'")
row = cursor.fetchone()
conn.close()

if row:
    username, hashed_password = row
    test_password = "admin123"
    is_valid = verify_password(test_password, hashed_password)
    print(f"User: {username}")
    print(f"Stored Hash: {hashed_password}")
    print(f"Test Password: {test_password}")
    print(f"Is Valid: {is_valid}")
    
    # Also test creating a new hash
    new_hash = get_password_hash(test_password)
    print(f"New Hash for '{test_password}': {new_hash}")
    print(f"Verify new hash: {verify_password(test_password, new_hash)}")
else:
    print("User 'admin' not found in database")
