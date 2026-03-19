# API Documentation

## Overview
This document provides an overview of the API endpoints. All endpoints go through the Gateway service.

## Services
1. [Gateway Service](#gateway-service)
2. [IAM Service](#iam-service)

---

## Gateway Service

### `GET /health`
- **Description:** Liveness check — confirms the Gateway process is running.
- **Response:**
  ```json
  { "status": "ok" }
  ```

### `POST /api/login`
- **Description:** Authenticate a user and obtain JWT tokens. Supports MFA/TOTP.
- **Request Body:**
  ```json
  {
    "username": "john_doe",
    "password": "password123",
    "totp": "123456"
  }
  ```
  `totp` is optional. Required only for users with MFA configured.
- **Response (success):**
  ```json
  {
    "access_token": "...",
    "expires_in": 36000,
    "refresh_expires_in": 1800,
    "refresh_token": "...",
    "user": { ... }
  }
  ```
- **Response (MFA setup required):** Returned when user has `CONFIGURE_TOTP` required action.
  ```json
  {
    "mfa_required": true,
    "mfa_action": "setup",
    "qr_code": "data:image/png;base64,...",
    "message": "Scan QR code with your authenticator app"
  }
  ```
- **Response (MFA setup complete):** Returned after verifying OTP during first-time setup.
  ```json
  {
    "mfa_required": true,
    "mfa_action": "setup_complete",
    "message": "MFA setup complete. Please login again with your OTP code."
  }
  ```
- **Response (OTP required):** Returned when user has MFA configured but no `totp` was provided.
  ```json
  {
    "mfa_required": true,
    "mfa_action": "verify",
    "message": "OTP code required"
  }
  ```

### `POST /api/refresh`
- **Description:** Refresh an expired access token using a refresh token.
- **Request Body:**
  ```json
  {
    "refresh_token": "..."
  }
  ```
- **Response:** Same shape as login.

### `POST /api/logout`
- **Description:** Revoke a refresh token (logout).
- **Request Body:**
  ```json
  {
    "refresh_token": "..."
  }
  ```
- **Response:**
  ```json
  {
    "message": "Logged out successfully"
  }
  ```

---

## IAM Service

### `GET /health`
- **Description:** Liveness check — confirms the IAM process is running.
- **Response:**
  ```json
  { "status": "ok" }
  ```

### `GET /readyz`
- **Description:** Readiness check — verifies MongoDB and Keycloak are reachable.
- **Response (ready):**
  ```json
  { "status": "ready", "checks": { "mongodb": true, "keycloak": true } }
  ```
- **Response (not ready):** Returns `503` with failed checks.
  ```json
  { "status": "not_ready", "checks": { "mongodb": true, "keycloak": false } }
  ```

All user endpoints below require `Authorization: Bearer <access_token>` header.

### `POST /api/user/create`
- **Description:** Create a new user. Requires admin role.
- **Request Body:**
  ```json
  {
    "user_name": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "roles": ["user"],
    "email": "john.doe@example.com",
    "enable_mfa": true,
    "organization_id": "optional-org-id"
  }
  ```
- **Note:** `roles` is required. Allowed values: `"user"`, `"admin"`, `"orgAdmin"`. `enable_mfa` is optional (default `false`). When `true`, the user will be required to set up TOTP on first login. `organization_id` is optional — when omitted the user is assigned to the default organization. systemAdmin users are not assigned to any organization.

### `PUT /api/user/update`
- **Description:** Update an existing user. If `user_id` is not provided, updates the requesting user's information. Only admins can change roles or update other users.
- **Request Body:**
  ```json
  {
    "user_id": "6770217c6c53e3cc94472273",
    "user_name": "john_doe_updated",
    "first_name": "Johnny",
    "last_name": "Doe",
    "email": "johnny.doe@example.com",
    "roles": ["user", "admin"]
  }
  ```
- **Note:** All fields are optional. Only provided fields will be updated. `roles` replaces the entire role list.

### `DELETE /api/user/delete/<user_id>`
- **Description:** Delete a user. Requires admin role.
- **Request Example:**
  ```
  /api/user/delete/6770217c6c53e3cc94472273
  ```

### `GET /api/user/get` or `GET /api/user/get/<user_id>`
- **Description:** Get a user by ID. If no ID is provided, returns the requesting user's information.
- **Request Example:**
  ```
  /api/user/get/6770217c6c53e3cc94472273
  ```
- **Note:** `user_id` is optional.

### `GET /api/user/get_by_keycloak_uid/<keycloak_uid>`
- **Description:** Get a user by their Keycloak UID. Requires systemAdmin role.
- **Request Example:**
  ```
  /api/user/get_by_keycloak_uid/a1b2c3d4-5678-...
  ```

### `GET /api/user/roles`
- **Description:** Get the list of available roles from Keycloak.
- **Request Example:**
  ```
  /api/user/roles
  ```

---

## Organization Endpoints

All organization endpoints require `Authorization: Bearer <access_token>` header.

### `POST /api/organization/create`
- **Description:** Create a new organization. Requires systemAdmin role.
- **Request Body:**
  ```json
  {
    "name": "Acme Corp",
    "description": "Main organization",
    "domains": ["acme.com"]
  }
  ```
- **Note:** `name` is required. `description` and `domains` are optional. A URL-friendly `slug` is generated from the name automatically.

### `PUT /api/organization/update`
- **Description:** Update an organization. Requires admin or orgAdmin role.
- **Request Body:**
  ```json
  {
    "org_id": "...",
    "name": "Acme Corp Updated",
    "description": "Updated description",
    "domains": ["acme.com", "acme.io"],
    "settings": {}
  }
  ```
- **Note:** All fields except `org_id` are optional.

### `DELETE /api/organization/delete/<org_id>`
- **Description:** Delete an organization. Requires systemAdmin role. The default organization cannot be deleted.

### `GET /api/organization/get` or `GET /api/organization/get/<org_id>`
- **Description:** Get an organization by ID, or list all organizations if no ID is provided.
- **Response (single):**
  ```json
  {
    "status": "success",
    "data": {
      "id": "...",
      "keycloak_org_id": "...",
      "name": "Acme Corp",
      "slug": "acme-corp",
      "description": "...",
      "domains": ["acme.com"],
      "is_default": false,
      "settings": {},
      "created_at": "...",
      "updated_at": "..."
    }
  }
  ```

### `POST /api/organization/add_user`
- **Description:** Add a user to an organization. Requires admin or orgAdmin role.
- **Request Body:**
  ```json
  {
    "org_id": "...",
    "user_id": "..."
  }
  ```

### `POST /api/organization/remove_user`
- **Description:** Remove a user from an organization. Requires admin or orgAdmin role.
- **Request Body:**
  ```json
  {
    "org_id": "...",
    "user_id": "..."
  }
  ```

### `GET /api/organization/members/<org_id>`
- **Description:** Get all members of an organization. Requires admin or orgAdmin role.
- **Response:**
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "...",
        "user_name": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
      }
    ]
  }
  ```
