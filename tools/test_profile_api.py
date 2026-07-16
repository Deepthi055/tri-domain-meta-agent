import os
import sys
import uuid
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8002")


def request(method, path, *, token=None, json_body=None, data=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, f"{BASE_URL}{path}", headers=headers, json=json_body, data=data)
    try:
        payload = response.json()
    except ValueError:
        payload = response.text
    return response, payload


def main():
    email = f"api-check-{uuid.uuid4().hex[:8]}@example.com"
    password = "secret123"

    print(f"Using base URL: {BASE_URL}")
    print(f"Registering user {email}")
    response, payload = request("post", "/auth/register", json_body={
        "name": "API Check",
        "email": email,
        "password": password,
    })
    if response.status_code not in (200, 201, 400):
        print("Registration failed", response.status_code, payload)
        sys.exit(1)
    if response.status_code == 400 and isinstance(payload, dict) and "already" in str(payload).lower():
        print("User already exists; continuing")

    print("Logging in")
    response, payload = request("post", "/auth/login", data={"username": email, "password": password})
    if response.status_code != 200:
        print("Login failed", response.status_code, payload)
        sys.exit(1)
    token = payload["access_token"]

    print("Fetching /auth/me")
    response, me_payload = request("get", "/auth/me", token=token)
    if response.status_code != 200:
        print("/auth/me failed", response.status_code, me_payload)
        sys.exit(1)

    print("Creating profile")
    create_payload = {
        "general": {"age": 33, "location": "Seattle"},
        "career": {"target_role": "Data Engineer"},
        "finance": {"monthly_income": 7000.0},
    }
    response, created = request("post", "/profile/create", token=token, json_body=create_payload)
    if response.status_code != 200:
        print("Profile create failed", response.status_code, created)
        sys.exit(1)

    print("GET /profile after create")
    response, fetched_after_create = request("get", "/profile", token=token)
    if response.status_code != 200:
        print("GET /profile failed after create", response.status_code, fetched_after_create)
        sys.exit(1)
    if fetched_after_create.get("general", {}).get("age") != 33:
        print("Unexpected age after create", fetched_after_create)
        sys.exit(1)

    print("Updating profile")
    update_payload = {
        "general": {"age": 34, "location": "Austin"},
        "career": {"target_role": "ML Engineer"},
        "finance": {"monthly_income": 8500.0, "monthly_expenses": 3200.0},
    }
    response, updated = request("put", "/profile", token=token, json_body=update_payload)
    if response.status_code != 200:
        print("Profile update failed", response.status_code, updated)
        sys.exit(1)

    print("GET /profile after update")
    response, fetched_after_update = request("get", "/profile", token=token)
    if response.status_code != 200:
        print("GET /profile failed after update", response.status_code, fetched_after_update)
        sys.exit(1)

    if fetched_after_update.get("general", {}).get("age") != 34:
        print("Unexpected age after update", fetched_after_update)
        sys.exit(1)
    if fetched_after_update.get("finance", {}).get("monthly_income") != 8500.0:
        print("Unexpected monthly income after update", fetched_after_update)
        sys.exit(1)

    print("API profile lifecycle check passed")
    print({
        "user": me_payload.get("email"),
        "created_age": fetched_after_create.get("general", {}).get("age"),
        "updated_age": fetched_after_update.get("general", {}).get("age"),
        "updated_income": fetched_after_update.get("finance", {}).get("monthly_income"),
    })


if __name__ == "__main__":
    main()
