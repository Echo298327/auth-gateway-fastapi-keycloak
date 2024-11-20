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
- **Request Body Example:**
  ```json
  {
    "user_name": "exampleUser",
    "first_name": "FirstName",
    "last_name": "LastName",
    "role_id": 1,
    "email": "example@example.com"
  }

#### 2. `POST {{GatewayApp}}/api/user/update`
- **Description:** Update an existing user.
- **Request Body Example:**
  ```json
  {
    "user_id": 1,
    "user_name": "exampleUser",
    "first_name": "FirstName",
    "last_name": "LastName",
    "email": "example@gmail.com"
  }
  
#### 3. `POST {{GatewayApp}}/api/user/delete`
- **Description:** Delete a user.
- **Request Body Example:**
  ```json
  {
    "user_id": 1
  }
  

#### 4. `POST {{GatewayApp}}/api/user/get`
- **Description:** Get a user by ID.
- **Request Body Example:**
  ```json
  {
    "user_id": 1
  }