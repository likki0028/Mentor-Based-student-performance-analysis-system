import requests

BASE = "http://localhost:8000"

# First login to get a token
login_res = requests.post(f"{BASE}/auth/login", data={"username": "student1", "password": "password123"})
print(f"Login status: {login_res.status_code}")
if login_res.status_code != 200:
    # Try different password
    login_res = requests.post(f"{BASE}/auth/login", data={"username": "student1", "password": "student123"})
    print(f"Login retry status: {login_res.status_code}")

if login_res.status_code == 200:
    token = login_res.json().get("access_token")
    print(f"Token obtained: {token[:20]}...")
    
    # Now test chatbot
    headers = {"Authorization": f"Bearer {token}"}
    chat_res = requests.post(
        f"{BASE}/chatbot/ask",
        json={"message": "What is my attendance?"},
        headers=headers
    )
    print(f"Chatbot status: {chat_res.status_code}")
    print(f"Chatbot response: {chat_res.text}")
else:
    print(f"Login failed: {login_res.text}")
    
    # Let's also check if /chatbot/ask endpoint exists at all (without auth)
    chat_res = requests.post(f"{BASE}/chatbot/ask", json={"message": "test"})
    print(f"Chatbot (no auth) status: {chat_res.status_code}")
    print(f"Chatbot (no auth) response: {chat_res.text}")
