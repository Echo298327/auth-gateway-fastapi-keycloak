# Authorization Guide

## Role System

### How Roles Work

Every user in the system has one or more **roles**. Roles control which API endpoints a user can access.

There are three default roles:

| Role | What it can do |
|------|---------------|
| `user` | View own profile, update own profile, get available roles |
| `admin` | Everything `user` can + create users, delete users, update other users, change roles |
| `systemAdmin` | Everything `admin` can + system-level operations (e.g. get user by Keycloak UID) |

### Users Can Have Multiple Roles

A user can have `["user", "admin"]` at the same time. Their access is the combination of what all their roles allow.

### AllowedRoles Enum

In `iam/src/domains/users/schemas/user.py`:

```python
class AllowedRoles(str, Enum):
    user = "user"
    admin = "admin"
```

This enum controls which roles can be assigned through the create/update user API. Only roles listed here are accepted.

`systemAdmin` is intentionally **not** in this enum. This means no one can assign `systemAdmin` through the API, not even an existing `systemAdmin`. The role is only assigned once, automatically, to the system admin account during the first startup. This prevents privilege escalation: an admin cannot promote themselves or others to `systemAdmin`.

When you add a new role, you must add it to this enum if you want it to be assignable through the API.

### System Admin

Created automatically on first startup using credentials from the environment config (`SYSTEM_ADMIN_USER_NAME`, `SYSTEM_ADMIN_PASSWORD`, etc.). Cannot be modified or deleted by other users. If a non-system-admin tries to access or change the system admin's data, the gateway returns 403.

### Where Roles Live

Roles exist in three places:

**Keycloak** — stores roles by name. This is what the JWT token and authorization checks use:

```
Keycloak Admin Console > Realm Roles:
  - user
  - admin
  - systemAdmin
```

When a user logs in, their roles appear in the JWT token under `realm_access.roles`:

```json
{
  "realm_access": {
    "roles": ["user", "default-roles-templaterealm"]
  }
}
```

**MongoDB (users collection)** — stores roles as Keycloak role **IDs** (UUIDs), not names:

```json
{
  "_id": ObjectId("..."),
  "keycloak_uid": "a1b2c3d4-...",
  "user_name": "john",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "roles": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
  "created_at": "2026-02-06T18:00:00",
  "updated_at": "2026-02-06T18:00:00"
}
```

The role IDs are resolved from Keycloak when creating or updating a user. The application uses these IDs internally (e.g. to check if a user is an admin).

**Authorization JSON files** — reference roles by name in policies:

```json
{
  "name": "Administrators-Access",
  "roles": ["admin", "systemAdmin"]
}
```

These names must match the role names in Keycloak exactly.

---

## Configuration Files

All authorization config lives in `iam/src/authorization/`:

```
iam/src/authorization/
  roles.json                  <-- Roles and policies (global)
  services/
    iam.json                  <-- Resources and permissions for IAM service
```

### roles.json

Two sections:

**realm_roles** — the roles that exist in the system:

```json
{
  "realm_roles": [
    { "name": "user", "description": "Standard user with limited access" },
    { "name": "admin", "description": "Administrator with elevated privileges" },
    { "name": "systemAdmin", "description": "System administrator with full access" }
  ]
}
```

**policies** — named groups of roles. A policy passes if the user has ANY of the listed roles:

```json
{
  "policies": [
    {
      "name": "Public-Access",
      "roles": ["user", "admin", "systemAdmin"]
    },
    {
      "name": "Administrators-Access",
      "roles": ["admin", "systemAdmin"]
    },
    {
      "name": "SystemAdmin-Access",
      "roles": ["systemAdmin"]
    }
  ]
}
```

### services/*.json

Each file defines API endpoints (**resources**) and which policies can access them (**permissions**).

Current `iam.json`:

```json
{
  "resources": [
    { "name": "user/create", "displayName": "Create User", "url": "/api/user/create" },
    { "name": "user/update", "displayName": "Update User", "url": "/api/user/update" },
    { "name": "user/delete", "displayName": "Delete User", "url": "/api/user/delete" },
    { "name": "user/get", "displayName": "Get User", "url": "/api/user/get" },
    { "name": "user/get_by_keycloak_uid", "displayName": "Get User by Keycloak UID", "url": "/api/user/get_by_keycloak_uid" },
    { "name": "user/roles", "displayName": "Get Roles", "url": "/api/user/roles" }
  ],
  "permissions": [
    {
      "name": "public",
      "policies": ["Public-Access"],
      "resources": ["user/update", "user/get", "user/roles"]
    },
    {
      "name": "Administrators",
      "policies": ["Administrators-Access"],
      "resources": ["user/create", "user/delete"]
    },
    {
      "name": "SystemAdmin",
      "policies": ["SystemAdmin-Access"],
      "resources": ["user/get_by_keycloak_uid"]
    }
  ]
}
```

This means:

| Endpoint | Who can access |
|----------|---------------|
| user/update, user/get, user/roles | All authenticated users |
| user/create, user/delete | admin, systemAdmin |
| user/get_by_keycloak_uid | systemAdmin only |

---

## How to Add a New Role

Example: adding a `manager` role.

### Step 1: Add the role in `roles.json`

```json
{
  "realm_roles": [
    { "name": "user", "description": "Standard user with limited access" },
    { "name": "admin", "description": "Administrator with elevated privileges" },
    { "name": "systemAdmin", "description": "System administrator with full access" },
    { "name": "manager", "description": "Manager with team-level access" }
  ]
}
```

### Step 2: Create a policy for it in `roles.json`

```json
{
  "name": "Managers-Access",
  "description": "Access for managers, admins, and system admins",
  "roles": ["manager", "admin", "systemAdmin"]
}
```

If you want ONLY managers to access (not admins, not systemAdmin), use:

```json
{
  "name": "Managers-Only",
  "roles": ["manager"]
}
```

### Step 3: Add it to `AllowedRoles` in `iam/src/domains/users/schemas/user.py`

```python
class AllowedRoles(str, Enum):
    user = "user"
    admin = "admin"
    manager = "manager"
```

Without this, the role cannot be assigned through the API.

### Step 4: Bump version and restart

Change `KEYCLOAK_CONFIG_VERSION` in `iam/src/core/config.py`:

```python
KEYCLOAK_CONFIG_VERSION: str = "0.0.2"  # was 0.0.1
```

Restart the services. The IAM service detects the version change and runs a full Keycloak sync.

---

## How to Add a New API Endpoint

Example: adding a `user/reports` endpoint that only admins can access.

### Step 1: Create the endpoint in the microservice

### Step 2: Add the resource and permission in `services/iam.json`

Add to `resources`:

```json
{ "name": "user/reports", "displayName": "User Reports", "url": "/api/user/reports" }
```

Add to `permissions` (or add the resource to an existing permission):

```json
{
  "name": "Administrators",
  "policies": ["Administrators-Access"],
  "resources": ["user/create", "user/delete", "user/reports"]
}
```

### Step 3: Bump `KEYCLOAK_CONFIG_VERSION` and restart

---

## How to Add a New Microservice

Example: adding an `orders` service.

### Step 1: Create a new JSON file `iam/src/authorization/services/orders.json`

```json
{
  "resources": [
    { "name": "order/create", "displayName": "Create Order", "url": "/api/order/create" },
    { "name": "order/get", "displayName": "Get Order", "url": "/api/order/get" },
    { "name": "order/delete", "displayName": "Delete Order", "url": "/api/order/delete" }
  ],
  "permissions": [
    {
      "name": "OrderPublic",
      "policies": ["Public-Access"],
      "resources": ["order/create", "order/get"]
    },
    {
      "name": "OrderAdmin",
      "policies": ["Administrators-Access"],
      "resources": ["order/delete"]
    }
  ]
}
```

All files in `services/` are loaded automatically. No changes needed in the initializer.

### Step 2: Add the service to the gateway service map

In `gateway/src/core/config.py`:

```python
self.SERVICE_MAP = {
    "user": self.IAM_URL,
    "order": self.ORDERS_URL,
}
```

And add `ORDERS_URL` to the environment config.

### Step 3: Bump `KEYCLOAK_CONFIG_VERSION` and restart

The gateway will route `/api/order/*` to the orders service and check authorization against the permissions defined in `orders.json`.

---

## Managing Roles Through the API

### Creating a User

```
POST /api/user/create
Authorization: Bearer <admin_token>
Body: {
  "user_name": "john",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "roles": ["user"]
}
```

- `roles` is required (no default)
- Only roles from `AllowedRoles` are accepted
- Only admins can create users

### Updating Roles

```
PUT /api/user/update
Authorization: Bearer <admin_token>
Body: {
  "user_id": "...",
  "roles": ["user", "admin"]
}
```

- `roles` replaces the entire role list
- Only admins can change roles
- Non-admin users can update their own name/email but not roles

### Removing a Role

Update with the roles you want to keep:

```json
{ "user_id": "...", "roles": ["user"] }
```

### Getting Available Roles

```
GET /api/user/roles
Authorization: Bearer <token>
```

Returns all roles from Keycloak. `systemAdmin` is hidden from non-system-admin users.

---

## Authentication Endpoints

### Login

```
POST /api/login
Body: { "username": "...", "password": "..." }
```

Returns access token, refresh token, expiration times, and user data.

### Refresh Token

```
POST /api/refresh
Body: { "refresh_token": "..." }
```

Returns new tokens without requiring login again.

### Logout

```
POST /api/logout
Body: { "refresh_token": "..." }
```

Revokes the refresh token so it can no longer be used.

---

## Config Versioning

`KEYCLOAK_CONFIG_VERSION` in `iam/src/core/config.py` controls when the full Keycloak sync runs.

- On startup, IAM compares the config version with the version stored in MongoDB (`service_versions` collection)
- If different: full sync (delete and recreate all roles, policies, resources, permissions in Keycloak)
- If same: skip, only verify Keycloak is reachable

**Bump the version** whenever you change `roles.json` or any file in `services/`.

---

## Quick Reference

| I want to... | What to do |
|--------------|-----------|
| Add a new role | Add to `roles.json` realm_roles + create a policy + add to `AllowedRoles` + bump version |
| Restrict endpoint to specific roles | Create/use a policy with those roles, attach it to the resource in a permission |
| Make endpoint accessible to everyone | Use the `Public-Access` policy |
| Add a new endpoint | Add resource + permission in the service JSON + bump version |
| Add a new microservice | Create a new JSON in `services/` + add to gateway service map + bump version |
| Assign a role to a user | `PUT /api/user/update` with `roles` field (admin only) |
| Remove a role from a user | `PUT /api/user/update` with the remaining roles |
