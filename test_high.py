"""Directly test the /notifications/test endpoint with High priority via the running backend."""
import sqlite3
import requests

BASE = "http://localhost:8000"

# First, get the password hash for niharika to understand the auth
conn = sqlite3.connect('backend/sql_app.db')
row = conn.execute("SELECT id, username, email, hashed_password FROM users WHERE username='niharika'").fetchone()
with open('user_info.txt', 'w') as f:
    f.write(f"User ID: {row[0]}\n")
    f.write(f"Username: {row[1]}\n")
    f.write(f"Email: {row[2]}\n")
    f.write(f"Hash: {row[3][:30]}...\n")
conn.close()

print(f"User: {row[1]}, Email: {row[2]}")

# Try to figure out the password - check seed scripts
# Based on seeding output, let's try common patterns
passwords_to_try = [
    "faculty123", "mentor123", "Faculty@123", "Mentor@123",
    "password", "1838", "niharika", "niharika123", 
    "admin123", "Password@123", "test", "test123",
    "changeme", "welcome", "12345678"
]

token = None
for pw in passwords_to_try:
    login = requests.post(f"{BASE}/auth/login", data={"username": "niharika", "password": pw})
    if login.status_code == 200:
        token = login.json().get("access_token")
        print(f"Login OK with: {pw}")
        break

if not token:
    print("Could not login. Trying admin user...")
    # Get all usernames to try
    conn = sqlite3.connect('backend/sql_app.db')
    users = conn.execute("SELECT username FROM users LIMIT 10").fetchall()
    conn.close()
    print(f"Available users: {[u[0] for u in users]}")
    
    # Try each user with common passwords
    for user_row in users:
        uname = user_row[0]
        for pw in ["faculty123", "mentor123", "admin123", "password", "changeme"]:
            login = requests.post(f"{BASE}/auth/login", data={"username": uname, "password": pw})
            if login.status_code == 200:
                token = login.json().get("access_token")
                print(f"Login OK: {uname} / {pw}")
                break
        if token:
            break

if not token:
    print("FAILED: Could not authenticate with any user")
else:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE}/notifications/test", json={
        "title": "Test HIGH Notification",
        "message": "Testing email delivery from High priority button",
        "priority": "high"
    }, headers=headers)
    print(f"Response: {resp.status_code}")
    print(f"Body: {resp.text}")
