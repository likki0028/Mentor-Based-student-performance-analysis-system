import requests

url = "http://127.0.0.1:8000/auth/login"
credentials = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "mentor", "password": "mentor123", "role": "mentor"},
    {"username": "lecturer", "password": "lecturer123", "role": "lecturer"},
    {"username": "student", "password": "student123", "role": "student"},
]

print("--- TESTING LOGIN API ---")
for cred in credentials:
    try:
        response = requests.post(url, data={"username": cred["username"], "password": cred["password"]})
        if response.status_code == 200:
            print(f"[SUCCESS] Login for {cred['username']} ({cred['role']})")
        else:
            print(f"[FAILURE] Login for {cred['username']} ({cred['role']}): {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] Login for {cred['username']}: {e}")
