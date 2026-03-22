import requests, json

r1 = requests.post('http://localhost:8000/auth/login', data={'username': 'admin', 'password': 'admin123'})
token = r1.json().get('access_token')

r2 = requests.get('http://localhost:8000/analytics/student/1', headers={'Authorization': f'Bearer {token}'})
data = r2.json()
subs = data.get('current_semester_details', {}).get('subjects', [])

print(f"TOTAL SUBJECTS IN SEM 6: {len(subs)}")
for s in subs:
    print(f"ID: {s.get('subject_id')} | Name: {s['subject_name']:<30} | Type: {s['subject_type']:<10} | Marks: {s['sessional_marks']}")
