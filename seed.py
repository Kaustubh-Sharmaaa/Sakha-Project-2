"""
Seed script — populates the in-memory DB with dummy data.
Run after starting the server:  python seed.py
"""
import httpx
import json

BASE = "http://localhost:8000/api/v1"


def log(label, res):
    try:
        body = res.json()
    except Exception:
        body = res.text
    status = "OK" if res.is_success else "FAIL"
    print(f"  [{status} {res.status_code}] {label}")
    if not res.is_success:
        print(f"           → {body}")
    return body


def seed():
    client = httpx.Client(base_url=BASE)

    print("\n── Auth ──────────────────────────────")

    # Admin user (creates new org → becomes admin automatically)
    res = client.post("/auth/register", json={
        "name": "Admin User",
        "email": "admin@mail.com",
        "password": "123456",
    })
    log("Register admin@mail.com", res)

    # Login as admin and grab token + org_id
    res = client.post("/auth/login", json={"email": "admin@mail.com", "password": "123456"})
    data = log("Login admin@mail.com", res)
    token = data["data"]["token"]
    org_id = data["data"]["user"]["orgId"]
    print(f"           org_id = {org_id}")

    headers = {"Authorization": f"Bearer {token}"}

    # Regular users in the same org
    regular_users = [
        {"name": "Alice Johnson",  "email": "alice@mail.com",  "password": "123456", "org_id": org_id},
        {"name": "Bob Smith",      "email": "bob@mail.com",    "password": "123456", "org_id": org_id},
        {"name": "Carol Williams", "email": "carol@mail.com",  "password": "123456", "org_id": org_id},
        {"name": "Dave Brown",     "email": "dave@mail.com",   "password": "123456", "org_id": org_id},
    ]

    print("\n── Users ─────────────────────────────")
    for u in regular_users:
        res = client.post("/auth/register", json=u)
        log(f"Register {u['email']}", res)

    print("\n── Verify list ───────────────────────")
    res = client.get("/users/", headers=headers)
    data = log("GET /users/", res)
    if res.is_success:
        for u in data["data"]:
            print(f"           {u['id']}  {u['email']}  ({u['role']})")

    print("\n── Done ──────────────────────────────\n")
    print(f"Admin token (copy into Postman {{{{token}}}}):\n{token}\n")


if __name__ == "__main__":
    seed()
