"""Test the /notifications/subscribe endpoint directly."""
import requests

BASE = "http://localhost:8000"

# Try niharika with seed-script passwords
for pw in ["1838", "faculty123", "mentor123", "Faculty@123", "Mentor@123"]:
    login = requests.post(f"{BASE}/auth/login", data={"username": "niharika", "password": pw})
    if login.status_code == 200:
        print(f"Login OK with password: {pw}")
        token = login.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try subscribing
        resp = requests.post(f"{BASE}/notifications/subscribe", json={
            "endpoint": "https://test.example.com/push/123",
            "p256dh": "test_p256dh_key_value",
            "auth": "test_auth_key"
        }, headers=headers)
        
        print(f"Subscribe response: {resp.status_code}")
        print(f"Body: {resp.text}")
        break
    else:
        print(f"Password '{pw}' failed: {login.text[:80]}")
else:
    print("All passwords failed")
