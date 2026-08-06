import json
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)
resp = client.post('/auth/register', json={'name':'Test User','email':'testuser@example.com','password':'secret123'})
print('STATUS', resp.status_code)
print(resp.text)
