# API Documentation

Base URL: `http://localhost:8000/api/v1`

All responses follow this shape:
- **Success:** `{ "success": true, "data": { ... } }`
- **Error:** `{ "success": false, "error": { "code": <status>, "message": "<reason>" } }`

Authenticated endpoints require the header:
```
Authorization: Bearer <token>
```

---

## Auth

### Register
`POST /auth/register`

Creates a new user. If no `org_id` is provided, a new organisation is created and the user becomes its admin. If an `org_id` is provided, the user joins that org as a regular user.

**Request**
```json
{
  "name": "Admin User",
  "email": "admin@mail.com",
  "password": "123456",
  "org_id": "optional — omit to create a new org"
}
```

**Response `201`**
```json
{
  "success": true,
  "data": {
    "id": "user:abc123",
    "name": "Admin User",
    "email": "admin@mail.com",
    "role": "admin",
    "orgId": "def456"
  }
}
```

**Errors**
| Code | Reason |
|------|--------|
| 400 | Email already registered |

---

### Login
`POST /auth/login`

Authenticates a user and returns an access token, refresh token, and user details.

**Request**
```json
{
  "email": "admin@mail.com",
  "password": "123456"
}
```

**Response `200`**
```json
{
  "success": true,
  "data": {
    "token": "<access_token>",
    "refresh_token": "<refresh_token>",
    "user": {
      "id": "user:abc123",
      "name": "Admin User",
      "email": "admin@mail.com",
      "role": "admin",
      "orgId": "def456"
    }
  }
}
```

**Errors**
| Code | Reason |
|------|--------|
| 401 | Invalid credentials |

---

### Refresh Token
`POST /auth/refresh`

Issues a new access token and refresh token using a valid refresh token.

**Request**
```json
{
  "refresh_token": "<refresh_token>"
}
```

**Response `200`**
```json
{
  "success": true,
  "data": {
    "token": "<new_access_token>",
    "refresh_token": "<new_refresh_token>"
  }
}
```

**Errors**
| Code | Reason |
|------|--------|
| 401 | Invalid or expired refresh token |

---

## Users

All user endpoints require a valid `Authorization` header. Endpoints marked **(admin)** reject requests from non-admin users with a `403`.

---

### Get Current User
`GET /users/me`

Returns the profile of the currently logged-in user.

**Response `200`**
```json
{
  "success": true,
  "data": {
    "id": "user:abc123",
    "name": "Admin User",
    "email": "admin@mail.com",
    "role": "admin",
    "orgId": "def456"
  }
}
```

---

### List Users (admin)
`GET /users/`

Returns all users in the admin's organisation.

**Response `200`**
```json
{
  "success": true,
  "data": [
    {
      "id": "user:abc123",
      "name": "Admin User",
      "email": "admin@mail.com",
      "role": "admin",
      "orgId": "def456"
    },
    {
      "id": "user:xyz789",
      "name": "Jane Doe",
      "email": "jane@mail.com",
      "role": "user",
      "orgId": "def456"
    }
  ]
}
```

---

### Create User (admin)
`POST /users/`

Admin creates a new user directly into their organisation. No password is required — a temporary one is set internally.

**Request**
```json
{
  "name": "Jane Doe",
  "email": "jane@mail.com",
  "role": "user"
}
```

**Response `201`**
```json
{
  "success": true,
  "data": {
    "id": "user:xyz789",
    "name": "Jane Doe",
    "email": "jane@mail.com",
    "role": "user",
    "orgId": "def456"
  }
}
```

**Errors**
| Code | Reason |
|------|--------|
| 400 | Email already registered |
| 403 | Admin access required |

---

### Update User (admin)
`PATCH /users/{any}`

Updates a user's name and/or role. The target user is identified by `user_id` in the request body — the URL path value is ignored.

**Request**
```json
{
  "user_id": "user:xyz789",
  "name": "Jane Smith",
  "role": "admin"
}
```

- `user_id` — required, ID of the user to update
- `name` — optional
- `role` — optional

**Response `200`**
```json
{
  "success": true,
  "data": {
    "id": "user:xyz789",
    "name": "Jane Smith",
    "email": "jane@mail.com",
    "role": "admin",
    "orgId": "def456"
  }
}
```

**Errors**
| Code | Reason |
|------|--------|
| 400 | No fields to update |
| 403 | Admin access required |
| 404 | User not found |

---

### Delete User (admin)
`DELETE /users/{id}`

Deletes a user from the organisation. The user ID can be passed either in the URL or in the request body — body takes precedence if both are provided.

**Option 1 — URL**
```
DELETE /users/user:xyz789
```

**Option 2 — Body**
```
DELETE /users/placeholder
```
```json
{
  "user_id": "user:xyz789"
}
```

**Response `200`**
```json
{
  "success": true,
  "data": {
    "message": "User deleted"
  }
}
```

**Errors**
| Code | Reason |
|------|--------|
| 403 | Admin access required |
| 404 | User not found |
