# Workflow Guide

A step-by-step guide for using the project — from first startup to managing users and adding new services.

> **Prerequisites:** Docker and Docker Compose installed, MongoDB running (locally or cloud). See the [README](../README.md) for full prerequisites.

---

## 1. Start the Project

```bash
docker compose up --build -d
```

On first startup the system automatically:
1. Creates the Keycloak realm, client, roles, policies, resources, and permissions
2. Creates a **system admin** account in both Keycloak and MongoDB
3. Sets up authorization configuration from the JSON files

Wait ~30-60 seconds for Keycloak to be ready. You can check the logs:

```bash
docker compose logs -f iam
```

When you see `IAM Service is running` — the system is ready.

---

## 2. Login as System Admin

The system admin credentials are configured in `.env.docker`:

```
POST http://localhost:8080/api/login
Content-Type: application/json

{
  "username": "sysadmin",
  "password": "sysadminpassword"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGci...",
  "expires_in": 36000,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGci...",
  "user": {
    "id": "...",
    "user_name": "sysadmin",
    "first_name": "None",
    "last_name": "None",
    "roles": ["<systemAdmin-role-id>"],
    "email": "sysadmin@dev.com"
  }
}
```

Save the `access_token` — you need it for all subsequent requests as `Authorization: Bearer <access_token>`.

> **Tip:** If using the included [Postman collection](../postman_collection.json), the login request automatically saves the token to a variable. All other requests use it automatically.

---

## 3. Create an Admin User

Only users with `admin` or `systemAdmin` roles can create new users.

```
POST http://localhost:8080/api/user/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_name": "admin_john",
  "first_name": "John",
  "last_name": "Doe",
  "roles": ["admin"],
  "email": "john@example.com"
}
```

**Response:**

```json
{
  "status": "success",
  "user_id": "...",
  "message": "User created successfully"
}
```

A random password is generated automatically. The admin can then log in and manage other users.

**Available roles for `roles` field:** `"user"`, `"admin"`. A user can have both: `["user", "admin"]`.

> **Note:** `systemAdmin` cannot be assigned through the API — it is created only once at system startup. See the [Authorization Guide](AUTHORIZATION_GUIDE.md) for details on the role system.

---

## 4. Create a Regular User

```
POST http://localhost:8080/api/user/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_name": "jane_smith",
  "first_name": "Jane",
  "last_name": "Smith",
  "roles": ["user"],
  "email": "jane@example.com"
}
```

Users with the `user` role can view and update their own profile, and view available roles.

---

## 5. Update a User

### Update Your Own Profile

Any logged-in user can update their own profile (no `user_id` needed):

```
PUT http://localhost:8080/api/user/update
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Johnson"
}
```

### Update Another User (Admin Only)

Admins can update any user by providing `user_id`:

```
PUT http://localhost:8080/api/user/update
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "<target-user-id>",
  "first_name": "Jane",
  "last_name": "Johnson"
}
```

### Change a User's Roles (Admin Only)

```
PUT http://localhost:8080/api/user/update
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "<target-user-id>",
  "roles": ["user", "admin"]
}
```

All fields are optional — only include what you want to change. Updatable fields: `user_name`, `first_name`, `last_name`, `email`, `roles`.

> **Note:** After a role change, the user needs to log in again to get a new token with the updated roles.

> **Note:** The system admin account cannot be updated by other users.

---

## 6. Get User Info

### Get Your Own Profile

```
GET http://localhost:8080/api/user/get
Authorization: Bearer <access_token>
```

### Get Another User's Profile (Admin Only)

```
GET http://localhost:8080/api/user/get/<user_id>
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "...",
    "user_name": "jane_smith",
    "first_name": "Jane",
    "last_name": "Johnson",
    "roles": ["<role-id>"],
    "email": "jane@example.com",
    "created_at": "2026-02-06T12:00:00"
  }
}
```

---

## 7. Get Available Roles

```
GET http://localhost:8080/api/user/roles
Authorization: Bearer <access_token>
```

Returns all realm roles. The `systemAdmin` role is hidden from non-system-admin users.

---

## 8. Delete a User (Admin Only)

```
DELETE http://localhost:8080/api/user/delete/<user_id>
Authorization: Bearer <access_token>
```

This deletes the user from both Keycloak and MongoDB.

> **Note:** The system admin cannot be deleted.

---

## 9. Refresh Token

Access tokens expire (default: 10 hours). Use the refresh token to get a new access token without logging in again:

```
POST http://localhost:8080/api/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

**Response:** Same shape as login — new `access_token`, `refresh_token`, and user data.

---

## 10. Logout

Invalidates the refresh token so it cannot be used again:

```
POST http://localhost:8080/api/logout
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

---

## 11. Add a New Service to the Gateway

The gateway forwards requests based on a **service map**. To add a new backend service (e.g. an `orders` service):

### Step 1 — Add the Service URL to Environment

In `.env.docker`, add:

```
ORDERS_URL=http://orders:8082
```

### Step 2 — Register in the Gateway Service Map

In `gateway/src/core/config.py`, add the service to the `SERVICE_MAP`:

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.SERVICE_MAP = {
        "user": self.IAM_URL,
        "orders": self.ORDERS_URL,   # new service
    }
```

And add the new setting field:

```python
class Settings(BaseSettings):
    IAM_URL: str
    ORDERS_URL: str       # new
    SERVICE_MAP: dict = {}
```

### Step 3 — Add the Service to Docker Compose

In `docker-compose.yml`, add the new service container.

### Step 4 — Add Authorization Config

Create `iam/src/authorization/services/orders.json` with resources and permissions for the new service's endpoints. Then bump `KEYCLOAK_CONFIG_VERSION` in `iam/src/core/config.py`.

See the [Authorization Guide](AUTHORIZATION_GUIDE.md) for the JSON format and how to set up roles/policies/permissions.

### How Gateway Routing Works

All requests to `/api/{service}/{action}` are routed by the gateway:

```
Client → GET /api/orders/list
                ↓
Gateway looks up "orders" in SERVICE_MAP → http://orders:8082
                ↓
Forwards to → GET http://orders:8082/list
```

The gateway handles JWT validation and Keycloak permission checks **before** forwarding. Your backend service receives the request with an `X-User` header containing the authenticated user's info.

---

## Quick Reference

| Action | Method | Endpoint | Who Can Do It |
|--------|--------|----------|---------------|
| Health check | `GET` | `/ping` | Anyone |
| Login | `POST` | `/api/login` | Anyone |
| Refresh token | `POST` | `/api/refresh` | Anyone (with valid refresh token) |
| Logout | `POST` | `/api/logout` | Anyone (with valid refresh token) |
| Create user | `POST` | `/api/user/create` | `admin`, `systemAdmin` |
| Update self | `PUT` | `/api/user/update` | Any logged-in user |
| Update other user | `PUT` | `/api/user/update` | `admin`, `systemAdmin` |
| Change roles | `PUT` | `/api/user/update` | `admin`, `systemAdmin` |
| Get own profile | `GET` | `/api/user/get` | Any logged-in user |
| Get other profile | `GET` | `/api/user/get/<id>` | `admin`, `systemAdmin` |
| Delete user | `DELETE` | `/api/user/delete/<id>` | `admin`, `systemAdmin` |
| Get available roles | `GET` | `/api/user/roles` | Any logged-in user |

---

## Related Documentation

- [API Documentation](API.md) — full endpoint reference with request/response schemas
- [Authorization Guide](AUTHORIZATION_GUIDE.md) — roles, policies, permissions, adding new roles/endpoints
- [Serverkit & Initializer Guide](SERVERKIT_GUIDE.md) — how the Keycloak initializer works, customizing the serverkit
- [Postman Collection](../postman_collection.json) — import into Postman to test all endpoints
