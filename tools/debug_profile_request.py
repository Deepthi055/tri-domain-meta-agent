import os
import uuid
import requests

BASE = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')
email = f'testui-{uuid.uuid4().hex[:8]}@example.com'
password = 'secret123'
print('Base URL:', BASE)
print('Registering', email)
resp = requests.post(f'{BASE}/auth/register', json={'name': 'UI Test', 'email': email, 'password': password})
print('register', resp.status_code, resp.text)
if resp.status_code not in (200, 201):
    raise SystemExit('register failed')
resp = requests.post(f'{BASE}/auth/login', data={'username': email, 'password': password})
print('login', resp.status_code, resp.text)
if resp.status_code != 200:
    raise SystemExit('login failed')
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
payload = {
    'general': {'age': 30, 'location': 'Testville'},
    'career': {'target_role': 'Tester'},
    'finance': {'monthly_income': 5000.0}
}
resp = requests.put(f'{BASE}/profile', json=payload, headers=headers)
print('put profile', resp.status_code, resp.text)
