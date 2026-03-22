import urllib.request
import urllib.parse
import json

url = "http://localhost:8000/auth/login"
data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode('ascii')
req = urllib.request.Request(url, data=data)
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        token = res.get('access_token')
except Exception as e:
    print(f"Login failed: {e}")
    exit(1)

url2 = "http://localhost:8000/analytics/student/196"
req2 = urllib.request.Request(url2, headers={'Authorization': f'Bearer {token}'})
try:
    with urllib.request.urlopen(req2) as response:
        print("Success:", response.read().decode('utf-8')[:200])
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    err_json = json.loads(err_body)
    print("DETAIL ERROR:", err_json.get("details"))
except Exception as e:
    print(f"Error: {e}")
