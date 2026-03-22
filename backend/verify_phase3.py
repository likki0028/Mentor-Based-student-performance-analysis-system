
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_phase3_endpoints():
    # 1. Login as Lecturer
    login_res = requests.post(f"{BASE_URL}/login", data={"username": "lecturer", "password": "lecturer123"})
    if login_res.status_code != 200:
        print("Login failed")
        return
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test /faculty/my-subjects
    subjects_res = requests.get(f"{BASE_URL}/faculty/my-subjects", headers=headers)
    print("My Subjects:", json.dumps(subjects_res.json(), indent=2))
    
    if subjects_res.status_code == 200 and len(subjects_res.json()) > 0:
        sub = subjects_res.json()[0]
        sub_id = sub["subject_id"]
        sec_id = sub["section_id"]
        
        # 3. Test /faculty/my-students with filters
        students_res = requests.get(f"{BASE_URL}/faculty/my-students?subject_id={sub_id}&section_id={sec_id}", headers=headers)
        print(f"Students for Sub {sub_id} Sec {sec_id}:", len(students_res.json()))
    else:
        print("No subjects found for lecturer. Ensure seed data was run with assignments/materials.")

if __name__ == "__main__":
    test_phase3_endpoints()
