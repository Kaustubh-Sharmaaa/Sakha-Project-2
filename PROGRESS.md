# Sakha-Project-2 — Development Progress

## What Was Built

### Project Overview
- **Name**: Sakha-Project-2 (FastAPI + SurrealDB + JWT multi-tenant SaaS backend)
- **Repo**: `github.com/Kaustubh-Sharmaaa/Sakha-Project-2` (private)
- **Status**: Day 1 scaffolding done; Day 2 features partially built, blocked by a SurrealDB query bug

### Architecture
- **Framework**: FastAPI with Pydantic v2
- **Database**: SurrealDB v1.0.8 (in-memory `mem://` for dev/testing)
- **Auth**: JWT access + refresh tokens (PyJWT + bcrypt)
- **Multi-tenancy**: `org_id`-based data isolation
- **RBAC**: `admin` and `user` roles (defined in `app/core/auth.py`)
- **API Versioning**: `/api/v1/...`
- **Logging**: Custom `log_requests` middleware in `main.py`
- **Global exception handler**: Catches all unhandled exceptions → 500

### File Structure
```
sakha-project-2/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, middleware, lifespan
│   ├── api/v1/
│   │   ├── auth.py                 # /register, /login, /refresh
│   │   ├── projects.py             # CRUD /projects/
│   │   ├── tasks.py                # CRUD /tasks/ (with project ownership check)
│   │   └── users.py                # /users/me, /users/ (admin-only)
│   ├── core/
│   │   ├── config.py               # Settings (Pydantic BaseSettings)
│   │   ├── security.py             # JWT + bcrypt utils
│   │   ├── auth.py                 # get_current_user, require_admin Depends
│   │   └── tenant.py               # OLD TenantMiddleware (deprecated, not used)
│   ├── db/
│   │   └── surrealdb.py            # init_db(), get_db(), in-memory SurrealDB
│   └── models/
│       └── schemas.py              # Pydantic models for all entities
├── tests/
│   ├── conftest.py                 # pytest-asyncio fixtures (setup_db, client)
│   ├── test_auth.py                # 7 tests — ALL PASSING
│   ├── test_users.py               # 4 tests — 2 failing
│   ├── test_projects.py            # 7 tests — 2 failing
│   └── test_tasks.py               # 8 tests — 5 failing
├── pytest.ini
├── requirements.txt
├── .env
└── PROJECT_PLAN.md                  # Full 3-day plan doc
```

## Critical Bug: SurrealDB Record ID Query Issue

### The Problem
SurrealDB (in-mem, embedded mode v1.0.8) stores a record with `id = 'user:abc'` as a `RecordID` object with:
- `table_name = 'user'`
- `id = 'abc'` (just the local part)

But when you create via `SET id = 'user:xxx'`, it stores:
- `table_name = 'user'`
- `id = 'user:xxx'` (full string, including table name prefix)

### The Query Bug
```sql
SELECT * FROM user WHERE id = 'user:xxx'   → Returns 0 rows
SELECT * FROM user WHERE id = user:xxx    → Returns 1 row
```

Using unquoted `user:xxx` (record literal syntax) works, but quoted `'`user:xxx'` doesn't.

**Confirmed working patterns:**
- `id = user:myuser123` (unquoted record literal) → matches correctly
- `id = 'myuser123'` → does NOT match
- `SELECT * FROM table` (no filter) → works fine, includes all records

**Impact**: All `get_project(id)`, `get_task(id)`, `get_me()` queries fail (404) because the `WHERE id = 'project:xxx'` pattern doesn't find records created with prefixed IDs.

### Current Workaround Applied
Created `_build_id_cond(field, record_id, default_table)` which generates:
```python
# For record_id = 'project:abc' → generates: "id = project:abc"  (unquoted)
# For record_id = 'abc'        → generates: "id = project:abc"  (assumes default table)
```

This uses unquoted record literal syntax in the SQL query. However, records created with `SET id = 'project:xxx'` store `record_id` as the full string `'project:xxx'`, which doesn't match when queried with `id = project:xxx`.

### Root Cause
The `CREATE project SET id = 'project:xxx'` syntax creates a RecordID where the `.id` property is `'project:xxx'` (full). The `id` field stores the full `table:local` form internally. But when you do `WHERE id = project:xxx` (unquoted), SurrealDB parses `project:xxx` as a record literal and matches because the stored id is exactly `project:xxx`.

Wait — let me re-check. When we do `SET id = 'project:xxx'` with the quotes in the SQL string, the `xxx` part becomes the RecordID's `id` field... Actually no, I need to verify this more carefully.

### More Investigation Needed
The workaround should work for **newly created** records. The failing tests are probably using IDs from records created earlier in the same test run (via `create_project` helper). But actually in the test environment each test gets a fresh `setup_db` fixture with `autouse=True`, so the DB is clean.

The issue may be that the token `sub` is `'user:abc123'` (with `user:` prefix), and when we do `_build_user_id_cond('user:abc123')` → generates `id = user:abc123` (unquoted). This **should** work according to our experiments.

## Tests Status

### Passing (17 tests)
- All 7 `test_auth.py` tests
- 2 `test_users.py` (get_me_admin, list_users_admin)
- 5 `test_projects.py` (create, list, list_empty, unauthenticated, unauthorized)
- 3 `test_tasks.py` (create_task_no_project, list_tasks_empty, list_tasks_filter_no_project)

### Failing (9 tests)
1. `test_get_project` — 404 (id query bug)
2. `test_update_project` — 404 (id query bug)
3. `test_create_task` — 404 project not found (project_id condition not matching)
4. `test_list_tasks` — returns empty instead of 2
5. `test_get_task` — KeyError on 'id'
6. `test_update_task` — KeyError on 'id'
7. `test_delete_task` — KeyError on 'id'
8. `test_get_me` — 404 user not found (id query bug)
9. `test_list_users_non_admin` — 200 instead of 403 (RBAC bug — `require_admin` isn't rejecting non-admins)

## RBAC Bug

`require_admin` in `app/core/auth.py` is returning 200 for non-admin users. This is strange because it should raise HTTPException(403). The issue might be that the JWT `role` claim isn't being set or read correctly.

Let me verify: when `register` creates a user, it sets `role = 'admin'` if no `org_id` provided (new org = first user = admin). But when `login` creates the token, `role` is included in the payload. The `get_current_user` and `require_admin` functions should read it correctly.

## Remaining Work

### Must Fix
1. **SurrealDB id query bug** — verify `_build_id_cond` generates correct queries and that newly created records can be fetched by id
2. **RBAC `require_admin`** — non-admin users are getting 200 on `/users/` instead of 403
3. **ALL tests must pass** before committing

### Day 2 Tasks (pending)
- Input sanitization for SQL injection (parameterized queries or ORM)
- Better RBAC enforcement
- Documentation / richer README

### Day 3 Tasks (pending)
- Docker setup
- CI pipeline
- Full test suite + coverage

## What Was Tried and Didn't Work

1. **TenantMiddleware → FastAPI Depends**: Replaced the middleware-based state injection with `get_current_user` dependency that decodes JWT in each handler. This fixed the `'State' object has no attribute 'org_id'` error.

2. **RecordID string conversion**: Tried `str()`, `repr()`, `RecordID.parse()`, and finally settled on `record_id.id` property to get the local ID part.

3. **SurrealDB query syntax**: Tested many forms — quoted strings don't work for record ID comparison; unquoted record literals (`id = table:record`) do work. Also discovered that `WHERE id = $var` (parameterized) doesn't work — need direct string interpolation.

## Key Code Notes

- `app/core/security.py` — `create_access_token`, `create_refresh_token`, `decode_token`, `get_password_hash`, `verify_password`
- `app/core/auth.py` — `get_current_user` (Depends), `require_admin` (Depends)
- `app/api/v1/auth.py` — uses `_v(val)` helper to extract `val.id` from RecordID objects
- `app/api/v1/projects.py` — `_build_id_cond("id", project_id)` generates `id = project:xxx`
- `app/api/v1/users.py` — `_build_user_id_cond(user["user_id"])` generates `id = user:xxx`
- `app/api/v1/tasks.py` — uses `_rec_id()` and `_build_id_cond()` for project_id and task id lookups

## Configuration

- `SECRET_KEY` = `sakha-secret-key-change-in-production-2024` (from env or default)
- `SURREALDB_URL` = `mem://` (in-memory, no persistent storage)
- `PYTHONPATH` must include project root for imports to work

## Commands to Run Tests

```bash
cd /home/ubuntu/.openclaw/workspace/sakha-project-2
PYTHONPATH=/home/ubuntu/.openclaw/workspace/sakha-project-2 python3 -m pytest tests/ -v
```

## Next Debugging Steps

1. Add debug print in `get_project` to see what query is being generated and what results come back
2. Test `require_admin` in isolation to see why non-admin passes
3. Verify that `create_project` returns a record that can be fetched back with `get_project` using the same id
4. Check if the `role` in the JWT token is being set and read correctly in `require_admin`
