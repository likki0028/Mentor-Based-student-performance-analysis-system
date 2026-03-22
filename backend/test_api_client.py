from fastapi.testclient import TestClient
from app.main import app
import json
import traceback

client = TestClient(app)

response = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
if response.status_code != 200:
    print("Login failed:", response.text)
else:
    token = response.json().get("access_token")
    try:
        response = client.get("/analytics/student/196", headers={"Authorization": f"Bearer {token}"})
        print(f"Status Code: {response.status_code}")
        print(response.text)
    except Exception as e:
        print("Server Exception Caught by TestClient:")
        traceback.print_exc()
