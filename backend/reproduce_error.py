import requests

url = "http://localhost:8000"
auth_res = requests.post(f"{url}/auth/login", data={"username": "sasibhanu", "password": "staff123"})
token = auth_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

results = []

# Test: datetime with time (the exact format from the frontend's datetime-local input)
payload = {"title": "ML Assignment Unit 3", "description": "Complete unit 3", "due_date": "2026-03-25T14:30:00", "subject_id": 7, "section_id": 1}
res = requests.post(f"{url}/assignments/", json=payload, headers=headers)
results.append(f"Create status: {res.status_code}")
results.append(f"Create response: {res.text}")

if res.status_code == 201:
    aid = res.json()["id"]
    results.append(f"\nAttaching file to assignment {aid}...")
    files = {'file': ('test.pdf', b'%PDF-1.4 test content', 'application/pdf')}
    res2 = requests.post(f"{url}/assignments/{aid}/attach-file", files=files, headers=headers)
    results.append(f"Attach status: {res2.status_code}")
    results.append(f"Attach response: {res2.text}")
    
    results.append(f"\nGetting assignment {aid}...")
    res3 = requests.get(f"{url}/assignments/{aid}", headers=headers)
    results.append(f"Get status: {res3.status_code}")
    results.append(f"Get response: {res3.text}")

with open("test_output.txt", "w") as f:
    f.write("\n".join(results))

print("Done!")
