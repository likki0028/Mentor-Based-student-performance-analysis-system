import requests, json

# Login as the student
r1 = requests.post('http://localhost:8000/auth/login', data={'username': '23241a6701', 'password': 'student123'})
if r1.status_code != 200:
    r1 = requests.post('http://localhost:8000/auth/login', data={'username': 'student', 'password': 'student123'})
print('Login status:', r1.status_code)

if r1.status_code == 200:
    token = r1.json().get('access_token')
    me = requests.get('http://localhost:8000/students/me', headers={'Authorization': 'Bearer ' + token})
    print('Me:', me.text[:200])
    sid = me.json().get('id')
    analytics = requests.get('http://localhost:8000/analytics/student/' + str(sid), headers={'Authorization': 'Bearer ' + token})
    print('Analytics status:', analytics.status_code)
    data = analytics.json()
    subs = data.get('current_semester_details', {}).get('subjects', [])
    print('Total Sem 6 Subjects:', len(subs))
    for s in subs[:3]:
        print(' ', s['subject_name'], ':', s['sessional_marks'])
