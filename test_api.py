"""Quick end-to-end test: login as student and hit the analytics endpoint."""
import requests

BASE = "http://localhost:8000"

# 1) Login
r = requests.post(f"{BASE}/auth/login", data={"username": "23241a6701", "password": "student123"})
print(f"Login: {r.status_code}")
if r.status_code != 200:
    print(f"  Body: {r.text}")
    exit(1)

token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2) Get student profile
r2 = requests.get(f"{BASE}/students/me", headers=headers)
print(f"Student/me: {r2.status_code}")
if r2.status_code == 200:
    stu = r2.json()
    print(f"  Student ID: {stu.get('id')}, Name: {stu.get('enrollment_number')}")
    sid = stu.get("id")
else:
    print(f"  Body: {r2.text[:300]}")
    exit(1)

# 3) Hit analytics
r3 = requests.get(f"{BASE}/analytics/student/{sid}", headers=headers)
print(f"Analytics: {r3.status_code}")
if r3.status_code != 200:
    print(f"  ERROR Body: {r3.text[:500]}")
else:
    print(f"  SUCCESS! Keys: {list(r3.json().keys())}")
