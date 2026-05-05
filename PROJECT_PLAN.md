# Sakha-Project-2 — Project Plan & Context

## Overview
Multi-Tenant SaaS Backend for Kaustubh. FastAPI + SurrealDB + JWT auth.

**Repo:** https://github.com/Kaustubh-Sharmaaa/Sakha-Project-2 (private)

## Tech Stack
| Layer | Choice |
|-------|--------|
| Backend | FastAPI (Python) |
| Database | SurrealDB (embedded in-memory) |
| Auth | JWT (access + refresh tokens) |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |

## 3-Day Plan

### Day 1 ✅ — Foundation
- Project setup + config
- SurrealDB connection layer
- Auth: register, login, refresh token
- Tenant middleware (org_id isolation via JWT)
- Users CRUD (GET /me, GET /users/)
- Projects CRUD
- Tasks CRUD
- Global error handler + request logging
- API versioning (/api/v1/...)
- Pushed to GitHub

### Day 2 🔜 — Testing & Polish
- Unit tests for all endpoints (auth, users, projects, tasks)
- Role-based access enforcement
- README with usage examples
- Edge case handling

### Day 3 — Deployment Prep
- Docker setup
- CI/CD pipeline
- Persistent SurrealDB setup (vs in-memory)
- API documentation cleanup

## Project Structure
```
sakha-project-2/
├── app/
│   ├── api/v1/
│   │   ├── auth.py       # register, login, refresh
│   │   ├── users.py      # me, list (admin)
│   │   ├── projects.py   # CRUD
│   │   └── tasks.py      # CRUD
│   ├── core/
│   │   ├── config.py     # Settings via pydantic-settings
│   │   ├── security.py   # JWT + password hashing
│   │   └── tenant.py     # Tenant middleware
│   ├── db/
│   │   └── surrealdb.py  # DB connection
│   ├── models/
│   │   └── schemas.py    # Pydantic models
│   └── main.py           # FastAPI app entry
├── tests/
├── requirements.txt
└── README.md
```

## Key Design Decisions
- **Multi-tenancy:** Every DB query filtered by `org_id` from JWT payload. TenantMiddleware attaches `request.state.org_id`, `request.state.user_id`, `request.state.role`.
- **Roles:** `admin` (full access) vs `user` (restricted). Middleware checks role for protected endpoints.
- **SurrealDB:** Currently using `mem://` (in-memory). Auth token check skips tenant middleware (public endpoints).
- **Testing:** Use `httpx.AsyncClient` with `app` fixture. DB initialized per test.

## Running the Server
```bash
cd sakha-project-2
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API Base URL
`http://localhost:8000/api/v1/`

## Auth Flow
1. `POST /api/v1/auth/register` → user + auto-generates org
2. `POST /api/v1/auth/login` → returns `access_token` + `refresh_token`
3. Use `Authorization: Bearer <access_token>` on all protected routes
4. `POST /api/v1/auth/refresh` → get new token pair

## Notes for Claude
- All DB queries in SurrealDB use raw query strings (`.query()`) — not ORM.
- SurrealDB query results are wrapped: `result[0].get("result", [])` to extract records.
- SQL injection risk in string formatting — TODO: use parameterized queries.
- Task creation requires project to belong to same org (enforced in handler).
- Admin-only endpoints: `GET /api/v1/users/` — raises 403 for non-admins.
- SurrealDB embedded mode may lose data on restart. Use `ws://` URL for persistence.
