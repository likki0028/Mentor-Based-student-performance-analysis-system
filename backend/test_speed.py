"""Test live API response times - write results to file."""
import requests
import time

BASE = "https://mspa-backend.onrender.com"
results = []

def timed_request(label, method, url, **kwargs):
    start = time.time()
    r = getattr(requests, method)(url, **kwargs)
    elapsed = time.time() - start
    line = f"{label}: {elapsed:.2f}s (status {r.status_code})"
    results.append(line)
    print(line)
    return r

print("=== Testing API Speed ===\n")
r = timed_request("Login (student)", "post", f"{BASE}/auth/login",
    data={"username": "23241a6701", "password": "student123"})

if r.status_code == 200:
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    timed_request("Student Dashboard", "get", f"{BASE}/students/dashboard", headers=headers)
    timed_request("Student Attendance", "get", f"{BASE}/attendance/student", headers=headers)
    timed_request("Student Marks", "get", f"{BASE}/marks/student", headers=headers)
    timed_request("Student Analytics", "get", f"{BASE}/analytics/student-performance", headers=headers)
    timed_request("Student Alerts", "get", f"{BASE}/alerts/", headers=headers)
else:
    results.append(f"Student login failed: {r.text[:200]}")

print("\n--- Lecturer ---")
r = timed_request("Login (lecturer)", "post", f"{BASE}/auth/login",
    data={"username": "sasibhanu", "password": "lecturer123"})
if r.status_code == 200:
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    timed_request("Lecturer Dashboard", "get", f"{BASE}/faculty/dashboard", headers=headers)
else:
    results.append(f"Lecturer login failed: {r.text[:200]}")

with open("speed_results.txt", "w") as f:
    f.write("\n".join(results))
print("\nResults saved to speed_results.txt")
