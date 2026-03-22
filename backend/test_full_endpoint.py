"""Test the full FastAPI endpoint with TestClient to get the real error"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=True)

# Login first
login_resp = client.post("/auth/login", data={"username": "23241a6701", "password": "student123"})
print("Login:", login_resp.status_code)
token = login_resp.json().get("access_token")

if token:
    resp = client.get("/analytics/student/1", headers={"Authorization": f"Bearer {token}"})
    print("Analytics status:", resp.status_code)
    print("Analytics response:", resp.text[:2000])
else:
    print("No token, login failed:", login_resp.text)
