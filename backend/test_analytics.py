import requests
import json

base_url = "http://127.0.0.1:8000"

# Login as student
login_data = {
    "username": "student",
    "password": "student123"
}
response = requests.post(f"{base_url}/auth/login", data=login_data)
if response.status_code != 200:
    print(f"Login failed {response.status_code}: {response.text}")
    import sys; sys.exit(1)

token = response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get student profile to find ID
print("Fetching profile...")
profile_res = requests.get(f"{base_url}/students/me", headers=headers)
if profile_res.status_code != 200:
    print(f"Failed to fetch profile: {profile_res.text}")
    exit(1)
student_id = profile_res.json()["id"]

# Get Analytics
print(f"Fetching analytics for student ID {student_id}...")
response = requests.get(f"{base_url}/analytics/student/{student_id}", headers=headers)
if response.status_code != 200:
    print(f"Failed to fetch analytics: {response.text}")
    exit(1)

data = response.json()

print(f"\n--- Analytics for {data['name']} ({data['enrollment_number']}) ---")
print(f"Current Semester: {data['current_semester']}")
print(f"CGPA: {data['cgpa']}")
print(f"Overall Attendance: {data['attendance_percentage']}%")

print("\n--- COMPLETED SEMESTERS (1-5) ---")
for sem in data.get('semester_stats', []):
    print(f"\nSemester {sem['semester']} - SGPA: {sem['sgpa']} - Attendance: {sem['attendance_percentage']}%")
    for sub in sem['subject_stats'][:3]: # print first 3
        print(f"  [{sub['subject_type']}] {sub['subject_name']}: {sub['grade_point']} GP, {sub['attendance_percentage']}% att")
    print("  ...")

print("\n--- CURRENT SEMESTER (6) ---")
curr = data.get('current_semester_details', {})
print(f"Semester {curr.get('semester', 'N/A')}")
for sub in curr.get('subjects', []):
    print(f"\n  [{sub['subject_type']}] {sub['subject_name']}")
    print(f"    Sessional Marks: {sub['sessional_marks']}")
    print(f"    Attendance: {sub['attendance_percentage']}%")
    if sub.get('assignment_count', 0) > 0:
        print(f"    Assignments ({sub['assignments_submitted']}/{sub['assignment_count']} submitted):")
        for a in sub['assignment_details']:
            print(f"      - {a['title']}: {a['status']} (Due: {a['due_date']})")

