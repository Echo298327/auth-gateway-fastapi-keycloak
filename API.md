# API Documentation

## Overview
This document provides an overview of the API endpoints. All endpoints go through the Gateway service.

## Services
1. [Gateway Service](#gateway-service)
2. [IAM Service](#iam-service)

---

## Gateway Service

### `GET /ping`
- **Description:** Health check.
- **Response:** `"pong!"`

### `POST /api/login`
- **Description:** Authenticate a user and obtain JWT tokens.
- **Request Body:**
  ```json
  {
    "username": "john_doe",
    "password": "password123"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "...",
    "expires_in": 36000,
    "refresh_expires_in": 1800,
    "refresh_token": "...",
    "user": { ... }
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

All IAM endpoints require `Authorization: Bearer <access_token>` header.

### `POST /api/user/create`
- **Description:** Create a new user. Requires admin role.
- **Request Body:**
  ```json
  {
    "user_name": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "roles": ["user"],
    "email": "john.doe@example.com"
  }
  ```
- **Note:** `roles` is required. Allowed values: `"user"`, `"admin"`.

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
