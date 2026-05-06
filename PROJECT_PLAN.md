# Sakha-Project-2 — Project Plan & Context

## Overview
Scalable REST API backend for Kaustubh. CRUD for users, projects, organisations. Testable via Postman.

**Repo:** https://github.com/Kaustubh-Sharmaaa/Sakha-Project-2 (private)

## Tech Stack
| Layer | Choice |
|-------|--------|
| Backend | FastAPI (Python) |
| Database | SurrealDB (persistent — `ws://` or file-based) |
| Auth | JWT (access + refresh tokens) |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |

## Project Structure
```
sakha-project-2/
├── app/
│   ├── api/v1/
│   │   ├── auth.py           # register, login, refresh
│   │   ├── users.py          # me, list (admin)
│   │   ├── projects.py       # CRUD
│   │   ├── organisations.py  # CRUD
│   │   └── tasks.py          # CRUD
│   ├── core/
│   │   ├── config.py         # Settings via pydantic-settings
│   │   ├── security.py       # JWT + password hashing
│   │   └── auth.py           # get_current_user, require_admin
│   ├── db/
│   │   └── surrealdb.py      # DB connection + pooling
│   ├── services/            # Business logic layer
│   │   ├── users.py
│   │   ├── projects.py
│   │   ├── organisations.py
│   │   └── tasks.py
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   └── main.py               # FastAPI app entry
├── tests/
├── requirements.txt
└── README.md
```

## API Endpoints

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`

### Users
- `GET /api/v1/users/me`
- `GET /api/v1/users/` (admin)
- `PATCH /api/v1/users/{id}` (admin)
- `DELETE /api/v1/users/{id}` (admin)

### Projects
- `GET /api/v1/projects/` — list all (filtered by org)
- `POST /api/v1/projects/`
- `GET /api/v1/projects/{id}`
- `PATCH /api/v1/projects/{id}`
- `DELETE /api/v1/projects/{id}`

### Organisations
- `GET /api/v1/organisations/` — list all
- `POST /api/v1/organisations/`
- `GET /api/v1/organisations/{id}`
- `PATCH /api/v1/organisations/{id}`
- `DELETE /api/v1/organisations/{id}`

### Tasks
- Same CRUD pattern as projects

## Scalability Considerations (Priority)
- [ ] Move from in-memory SurrealDB (`mem://`) to persistent storage (`ws://` or file-based)
- [ ] Pagination on all list endpoints (`limit`, `offset`)
- [ ] Async throughout (FastAPI + SurrealDB async driver)
- [ ] Proper DB connection pooling
- [ ] Rate limiting (optional but noted)
- [ ] Clean layered architecture: routers → services → db
- [ ] Parameterized queries (SQL injection prevention)

## Running the Server
```bash
cd sakha-project-2
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API Base URL
`http://localhost:8000/api/v1/`

## Notes
- More details to be added as requirements come in
