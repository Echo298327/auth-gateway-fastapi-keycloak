# API Documentation

## Overview
This document provides an overview of the API endpoints for the microservices in this project. Each microservice is listed below with its respective routes and usage.

## Services
1. [Gateway Service](#gateway-service)
2. [Users Service](#users-service)

---

## Users Service

### Endpoints

#### 1. `POST {{GatewayApp}}/api/user/create`
- **Description:** Create a new user.
- **Method:** POST
- **Request Body Example:**
  ```json
  {
    "user_name": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "roles": ["user", "admin"],
    "email": "john.doe@example.com"
  }
  ```

#### 2. `PUT {{GatewayApp}}/api/user/update`
- **Description:** Update an existing user. If user_id is not provided, updates the requesting user's information.
- **Method:** PUT
- **Request Body Example:**
  ```json
  {
    "user_id": "6770217c6c53e3cc94472273",
    "user_name": "john_doe_updated",
    "first_name": "Johnny",
    "last_name": "Doe",
    "email": "johnny.doe@example.com",
    "roles": ["user"]
  }
  ```
- **Note:** All fields are optional. Only provided fields will be updated.

#### 3. `DELETE {{GatewayApp}}/api/user/delete/<user_id>`
- **Description:** Delete a user.
- **Method:** DELETE
- **Request Example:**
  ```
  {{GatewayApp}}/api/user/delete/<user_id>
  ```


#### 4. `GET {{GatewayApp}}/api/user/get<user_id>`
- **Description:** Get a user by ID. If no ID is provided, returns the requesting user's information.
- **Method:** GET
- **Request Example:**
  ```
  {{GatewayApp}}/api/user/get/<user_id>
  ```
- **Note:** Query parameter is optional

#### 5. `GET {{GatewayApp}}/api/user/get_by_keycloak_uid/<keycloak_uid>`
- **Description:** Get a user by their Keycloak UID.
- **Method:** GET
- **Request Example:**
  ```
  {{GatewayApp}}/api/user/get_by_keycloak_uid/<keycloak_uid>
  ```

### Notes
- All fields marked as optional can be omitted from the request
- Email addresses must be in valid format
- Available roles: ["user", "admin"] (example roles, adjust as needed)
