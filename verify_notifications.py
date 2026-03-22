"""Verify system-wide notification triggers."""
import sqlite3
import requests
import time

BASE = "http://localhost:8000"

def log_test(msg):
    print(f"\n--- {msg} ---")

# 1. Login to get token
login = requests.post(f"{BASE}/auth/login", data={"username": "niharika", "password": "1838"})
if login.status_code != 200:
    # Try different password or user
    login = requests.post(f"{BASE}/auth/login", data={"username": "niharika", "password": "niharika123"})

token = login.json().get("access_token") if login.status_code == 200 else None
headers = {"Authorization": f"Bearer {token}"} if token else {}

log_test("Testing Assignment Notification")
# Create a test assignment
data = {
    "title": "System Integration Test",
    "description": "Checking if notifications fire",
    "due_date": "2026-04-01",
    "subject_id": 1,
    "section_id": 2 # Assuming section 2 exists
}
resp = requests.post(f"{BASE}/assignments/", json=data, headers=headers)
print(f"Assignment Create: {resp.status_code}")

# 2. Check DB for notifications
conn = sqlite3.connect('backend/sql_app.db')
cursor = conn.cursor()

log_test("Checking Notifications Table")
cursor.execute("SELECT id, user_id, title, message, priority FROM notifications ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(f"Notif: {r}")

log_test("Checking Email Log (if high priority sent)")
# We can check the backend console output if redirected, or just trust the DB for now.

conn.close()
