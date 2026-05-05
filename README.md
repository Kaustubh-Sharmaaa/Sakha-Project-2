# Sakha-Project-2
Multi-Tenant SaaS Backend — FastAPI + SurrealDB

## Tech Stack
- **FastAPI** — Modern Python web framework
- **SurrealDB** — Multi-model embedded database with native multi-tenancy
- **JWT** — Token-based authentication (access + refresh tokens)
- **Pydantic v2** — Data validation and settings management

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

## API Endpoints (v1)

### Auth
- `POST /api/v1/auth/register` — Register a new user
- `POST /api/v1/auth/login` — Login and get tokens
- `POST /api/v1/auth/refresh` — Refresh access token

### Users
- `GET /api/v1/users/me` — Get current user
- `GET /api/v1/users/` — List users in your org (admin only)

### Projects
- `POST /api/v1/projects/` — Create project
- `GET /api/v1/projects/` — List projects
- `GET /api/v1/projects/{id}` — Get project
- `PATCH /api/v1/projects/{id}` — Update project
- `DELETE /api/v1/projects/{id}` — Delete project

### Tasks
- `POST /api/v1/tasks/` — Create task
- `GET /api/v1/tasks/` — List tasks (optional: ?project_id=...)
- `GET /api/v1/tasks/{id}` — Get task
- `PATCH /api/v1/tasks/{id}` — Update task
- `DELETE /api/v1/tasks/{id}` — Delete task

## Architecture
- **Multi-tenancy**: Every data query is scoped by `org_id` from the JWT token
- **RBAC**: Admin role required for user management endpoints
- **API Versioning**: All endpoints live under `/api/v1/`
