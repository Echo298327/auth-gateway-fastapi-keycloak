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

## 9. MFA / Two-Factor Authentication

### Create a User with MFA Enabled

Add `"enable_mfa": true` when creating a user:

```
POST http://localhost:8080/api/user/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_name": "secure_user",
  "first_name": "Secure",
  "last_name": "User",
  "roles": ["user"],
  "email": "secure@example.com",
  "enable_mfa": true
}
```

The user will have a `CONFIGURE_TOTP` required action in Keycloak.

### First Login (MFA Setup)

**Step 1** — User logs in normally:

```
POST http://localhost:8080/api/login
Content-Type: application/json

{ "username": "secure_user", "password": "<password>" }
```

**Response** — QR code for authenticator app:

```json
{
  "mfa_required": true,
  "mfa_action": "setup",
  "qr_code": "data:image/png;base64,...",
  "message": "Scan QR code with your authenticator app"
}
```

**Step 2** — User scans the QR code with Google Authenticator / Authy, then sends the OTP:

```
POST http://localhost:8080/api/login
Content-Type: application/json

{ "username": "secure_user", "password": "<password>", "totp": "123456" }
```

**Response:**

```json
{
  "mfa_required": true,
  "mfa_action": "setup_complete",
  "message": "MFA setup complete. Please login again with your OTP code."
}
```

**Step 3** — User logs in again with a fresh OTP:

```
POST http://localhost:8080/api/login
Content-Type: application/json

{ "username": "secure_user", "password": "<password>", "totp": "654321" }
```

**Response** — normal login response with tokens.

### Regular Login with MFA

After setup, every login requires all three fields:

```
POST http://localhost:8080/api/login
Content-Type: application/json

{ "username": "secure_user", "password": "<password>", "totp": "123456" }
```

If `totp` is omitted, the gateway returns:

```json
{ "mfa_required": true, "mfa_action": "verify", "message": "OTP code required" }
```

---

## 10. Organization Management

Organizations enable multi-tenancy — users belong to one or more organizations.

### How It Works

- A **default organization** is created automatically on first startup
- New users are assigned to the default organization (unless a specific `organization_id` is provided)
- `systemAdmin` is org-free — it manages organizations but doesn't belong to any
- Users can belong to multiple organizations
- Role hierarchy: `systemAdmin` (platform) → `orgAdmin` (org-level) → `admin` → `user`

### Create an Organization (systemAdmin only)

```
POST http://localhost:8080/api/organization/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Acme Corp",
  "description": "Main organization",
  "domains": ["acme.com"]
}
```

### List All Organizations

```
GET http://localhost:8080/api/organization/get
Authorization: Bearer <access_token>
```

### Add a User to an Organization

```
POST http://localhost:8080/api/organization/add_user
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "org_id": "<org-id>",
  "user_id": "<user-id>"
}
```

### Remove a User from an Organization

```
POST http://localhost:8080/api/organization/remove_user
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "org_id": "<org-id>",
  "user_id": "<user-id>"
}
```

### Get Organization Members

```
GET http://localhost:8080/api/organization/members/<org_id>
Authorization: Bearer <access_token>
```

### Create a User in a Specific Organization

```
POST http://localhost:8080/api/user/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_name": "jane_smith",
  "first_name": "Jane",
  "last_name": "Smith",
  "roles": ["user"],
  "email": "jane@acme.com",
  "organization_id": "<org-id>"
}
```

### Delete an Organization (systemAdmin only)

```
DELETE http://localhost:8080/api/organization/delete/<org_id>
Authorization: Bearer <access_token>
```

> **Note:** The default organization cannot be deleted.

---

## 11. Refresh Token

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

## 12. Logout

Invalidates the refresh token so it cannot be used again:

```
POST http://localhost:8080/api/logout
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

---

## 13. Add a New Service to the Gateway

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
| Health (Gateway) | `GET` | `/health` | Anyone |
| Health (IAM) | `GET` | `/health` | Anyone |
| Readiness (IAM) | `GET` | `/readyz` | Anyone |
| Login | `POST` | `/api/login` | Anyone (optional `totp` for MFA) |
| Refresh token | `POST` | `/api/refresh` | Anyone (with valid refresh token) |
| Logout | `POST` | `/api/logout` | Anyone (with valid refresh token) |
| Create user | `POST` | `/api/user/create` | `admin`, `orgAdmin`, `systemAdmin` |
| Update self | `PUT` | `/api/user/update` | Any logged-in user |
| Update other user | `PUT` | `/api/user/update` | `admin`, `orgAdmin`, `systemAdmin` |
| Change roles | `PUT` | `/api/user/update` | `admin`, `orgAdmin`, `systemAdmin` |
| Get own profile | `GET` | `/api/user/get` | Any logged-in user |
| Get other profile | `GET` | `/api/user/get/<id>` | `admin`, `orgAdmin`, `systemAdmin` |
| Delete user | `DELETE` | `/api/user/delete/<id>` | `admin`, `orgAdmin`, `systemAdmin` |
| Get available roles | `GET` | `/api/user/roles` | Any logged-in user |
| Create organization | `POST` | `/api/organization/create` | `systemAdmin` |
| Update organization | `PUT` | `/api/organization/update` | `admin`, `orgAdmin`, `systemAdmin` |
| Delete organization | `DELETE` | `/api/organization/delete/<id>` | `systemAdmin` |
| Get organization(s) | `GET` | `/api/organization/get[/<id>]` | Any logged-in user |
| Add user to org | `POST` | `/api/organization/add_user` | `admin`, `orgAdmin`, `systemAdmin` |
| Remove user from org | `POST` | `/api/organization/remove_user` | `admin`, `orgAdmin`, `systemAdmin` |
| Get org members | `GET` | `/api/organization/members/<id>` | `admin`, `orgAdmin`, `systemAdmin` |

---

## Related Documentation

- [API Documentation](API.md) — full endpoint reference with request/response schemas
- [Authorization Guide](AUTHORIZATION_GUIDE.md) — roles, policies, permissions, adding new roles/endpoints
- [Serverkit & Initializer Guide](SERVERKIT_GUIDE.md) — how the Keycloak initializer works, customizing the serverkit
- [Postman Collection](../postman_collection.json) — import into Postman to test all endpoints
