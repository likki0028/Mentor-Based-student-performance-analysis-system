
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_alert_flow():
    # 1. Login as mentor_b
    print("Logging in as mentor_b...")
    login_data = {"username": "mentor_b", "password": "mentor123"}
    resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Add low marks for student 21 (sectionb_stu_1)
    # mentor_b is the mentor for Section B.
    print("Adding low marks for student 21 via API...")
    marks_data = {
        "marks": [
            {
                "student_id": 21,
                "subject_id": 1,
                "assessment_type": "internal",
                "score": 5,
                "total": 100
            }
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/marks/", json=marks_data, headers=headers)
    if resp.status_code == 201:
        print(f"Success: {resp.json()['message']}")
    else:
        print(f"Failed to add marks: {resp.text}")

if __name__ == "__main__":
    test_api_alert_flow()
