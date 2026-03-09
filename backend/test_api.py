"""Full API verification test — all endpoints."""
import requests

BASE = "http://localhost:8001"

print("=" * 60)
print("FULL API VERIFICATION")
print("=" * 60)

# 1. Root
r = requests.get(f"{BASE}/")
print(f"\n[ROOT] GET / -> {r.status_code}: {r.json()}")

# 2. Login as student1
r = requests.post(f"{BASE}/auth/login", data={"username": "student1", "password": "student123"})
print(f"\n[AUTH] POST /auth/login (student1) -> {r.status_code}")
student_token = r.json().get("access_token") if r.status_code == 200 else None
headers_s = {"Authorization": f"Bearer {student_token}"} if student_token else {}

# 3. Student endpoints
r = requests.get(f"{BASE}/students/me", headers=headers_s)
print(f"[STUDENT] GET /students/me -> {r.status_code}: {r.json()}")

r = requests.get(f"{BASE}/students/1/attendance", headers=headers_s)
print(f"[STUDENT] GET /students/1/attendance -> {r.status_code}: {len(r.json())} records")

r = requests.get(f"{BASE}/students/1/marks", headers=headers_s)
print(f"[STUDENT] GET /students/1/marks -> {r.status_code}: {len(r.json())} records")

# 4. Student alerts
r = requests.get(f"{BASE}/alerts/", headers=headers_s)
print(f"[ALERTS] GET /alerts/ (student) -> {r.status_code}: {len(r.json())} alerts")

# 5. Login as admin
r = requests.post(f"{BASE}/auth/login", data={"username": "admin", "password": "admin123"})
print(f"\n[AUTH] POST /auth/login (admin) -> {r.status_code}")
admin_token = r.json().get("access_token") if r.status_code == 200 else None
headers_a = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

# 6. Faculty endpoints
r = requests.get(f"{BASE}/faculty/dashboard", headers=headers_a)
print(f"[FACULTY] GET /faculty/dashboard -> {r.status_code}: {r.json()}")

r = requests.get(f"{BASE}/faculty/my-students", headers=headers_a)
print(f"[FACULTY] GET /faculty/my-students -> {r.status_code}: {len(r.json())} students")

# 7. Faculty remarks
r = requests.post(f"{BASE}/faculty/remarks", json={"student_id": 1, "message": "Great progress!"}, headers=headers_a)
print(f"[FACULTY] POST /faculty/remarks -> {r.status_code}: {r.json()}")

r = requests.get(f"{BASE}/faculty/remarks/1", headers=headers_a)
print(f"[FACULTY] GET /faculty/remarks/1 -> {r.status_code}: {len(r.json())} remarks")

# 8. Attendance report
r = requests.get(f"{BASE}/attendance/report", headers=headers_a)
print(f"[ATTENDANCE] GET /attendance/report -> {r.status_code}: {len(r.json())} entries")

# 9. Generate alerts
r = requests.post(f"{BASE}/alerts/generate", headers=headers_a)
print(f"[ALERTS] POST /alerts/generate -> {r.status_code}: {r.json()}")

# 10. Register new user (admin only)
r = requests.post(f"{BASE}/auth/register", json={"username": "newstudent99", "password": "pass123", "role": "student"}, headers=headers_a)
print(f"[AUTH] POST /auth/register -> {r.status_code}: {r.json()}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
