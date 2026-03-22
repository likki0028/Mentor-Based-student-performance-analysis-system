import requests
import json

url = "http://127.0.0.1:8000/auth/login"
data = {
    "username": "admin",
    "password": "admin123"
}

print(f"Testing login for admin at {url}")
try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
