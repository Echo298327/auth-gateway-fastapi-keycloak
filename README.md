# FastAPI Microservices Starter Template

This repository provides a starter template for building scalable microservices using FastAPI, Docker Compose, and Keycloak for authentication and user management. It includes a gateway app, a user manager, and a pre-configured environment for quick project initialization.

## Features

- **Gateway App:** Acts as an API Gateway, routing requests to appropriate microservices.
- **User Manager:** Handles user authentication and management, integrated with Keycloak.
- **Keycloak Integration:** Simplifies authentication and role-based access control.
- **Docker Compose:** Pre-configured to orchestrate services effortlessly.
- **Environment Configuration:** Easily adjustable via `.env` files.
- **Extensible Architecture:** Add more microservices as your project grows.

---

## Database
This project uses MongoDB as the primary database for storing information.
The user microservice (users) connects to a MongoDB instance, which is configurable via environment variables.

Ensure you have MongoDB running locally, or use a cloud-hosted MongoDB service.

## Documentation
- [API Documentation](API.md) - Complete API endpoint reference
- [Authorization Guide](AUTHORIZATION_GUIDE.md) - Detailed authorization system explanation
- [Postman Collection](postman_collection.json) - Ready-to-use API testing collection

You can use the Postman collection provided to test the API endpoints easily. Import the `postman_collection.json` file into Postman to get started.

## Getting Started

### Prerequisites

Make sure you have the following installed:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.10+](https://www.python.org/)
- [MongoDB](https://www.mongodb.com/products/platform/atlas-database)
- Git CLI

---

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Echo298327/auth-gateway-fastapi-keycloak.git
   cd auth-gateway-fastapi-keycloak
   ```

2. **Configure Environment Variables:**
   - The project includes two `.env` files for different use cases:
     - `.env.docker`: Used when running the application with Docker Compose. This file is automatically handled by the `docker-compose.yml` configuration, and no additional setup is required.
     - `.env`: Used for local development without Docker Compose. You can use the `.env.example` file as a template to create your own `.env` file.

     **Note:**
     - If you are using Docker Compose, the `.env.docker` file will provide the necessary environment variables.
     - If you plan to run services locally without Docker Compose, ensure the `.env` file is properly configured.
     - For local development, services such as Postgres, Keycloak, and optionally PgAdmin must still be run using Docker Compose. You can comment out unnecessary services in the `docker-compose.yml` file if not required.

3. Start the services using Docker Compose:

   ```bash
   docker-compose up --build
   ```

4. Access the services:

   - **Gateway App:** [http://localhost:8080](http://localhost:8080)
   - **Keycloak Admin Console:** [http://localhost:9000](http://localhost:9000)

---

## Project Structure

```plaintext
│   .env
│   .env.docker
│   API.md
│   docker-compose.yml
│   LICENSE
│   postman_collection.json
│   README.md
│   SECURITY.md
│
├───.github
│   │   CODEOWNERS
│   │
│   └───workflows
│           run-tests.yml
│
├───deployment
│   │   pgadmin_server.json
│   │
│   └───docker
│           gateway_dockerfile
│           keycloak_dockerfile
│           users_dockerfile
│
├───gateway
│   │   requirements.txt
│   │   __init__.py
│   │
│   ├───src
│   │   │   app.py
│   │   │   config.py
│   │   │   manager.py
│   │   │   __init__.py
│   │
│   └───test
│           __init__.py
│
└───users
    │   requirements.txt
    │
    ├───src
    │   │   app.py
    │   │   config.py
    │   │   keycloak_config.json
    │   │   manager.py
    │   │   mongo_models.py
    │   │   schemas.py
    │   │   __init__.py
    │   └───authorization
    │       │   roles.json
    │       │
    │       └───services
    │           │   users.json
    │
    └───test
        │   test_manager.py
        │   __init__.py
```

---

### Environment Variables

The `.env` files contain configurations for running the application:

- **`.env.docker`**: Used by Docker Compose. This file provides pre-configured environment variables to ensure seamless container orchestration.
- **`.env`**: Used for local development when running services outside Docker Compose. Configure this file to match your local setup.

Ensure you select the appropriate file based on your use case.

---

## Authentication & Login

### System Admin Login

The system automatically creates a default system administrator account during initialization. You can log in using:

**Default System Admin Credentials:**
```
Username: sysadmin
Password: [Set via SYSTEM_ADMIN_PASSWORD environment variable]
```

**Note:** The system admin credentials are configured through environment variables. Check your `.env` or `.env.docker` file for the actual password.

### Login Process

#### 1. **API Login Endpoint**
```
POST /api/login
Content-Type: application/json

{
    "username": "sysadmin",
    "password": "your-system-admin-password"
}
```

#### 2. **Response Format**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "refresh_expires_in": 86400,
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": "user_id",
        "user_name": "sysadmin",
        "email": "admin@example.com",
        "roles": ["64f8a1b2c3d4e5f6a7b8c9d0"]
    }
}
```


#### 3. **Using the Access Token**
Include the access token in the Authorization header for subsequent requests:
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 4. **Postman Integration**
When using the provided Postman collection:
1. **Automatic Token Management**: After successful login, the access token is automatically saved to Postman environment variables
2. **Auto-Authentication**: All subsequent requests in the collection will automatically use the saved token
3. **Environment Variable**: The token is stored as `{{access_token}}` in your Postman environment
4. **No Manual Setup**: You don't need to manually copy/paste tokens between requests

**Postman Workflow:**
```
1. Import postman_collection.json
2. Run the Login request
3. ✅ Token automatically saved to environment
4. All other requests now work automatically
```

### User Roles

The system comes with three default user roles, but the entire role system can be customized and extended:

**Default Roles:**
- **`user`**: Basic user with limited permissions
- **`admin`**: Administrator with user management capabilities  
- **`systemAdmin`**: System administrator with full access (cannot be modified by others)

**Fully Customizable Role System:**
- ✅ **Add new roles**: Create custom roles like `moderator`, `editor`, `viewer`, etc.
- ✅ **Modify existing roles**: Change permissions for `user`, `admin`, or `systemAdmin`
- ✅ **Remove default roles**: Delete roles you don't need (except `systemAdmin`)
- ✅ **Custom permissions**: Define exactly what each role can access
- ✅ **Hierarchical structure**: Define role inheritance and access levels
- ✅ **Dynamic assignment**: Users can have multiple roles simultaneously

For detailed instructions on adding new roles and customizing permissions, see the [Authorization Guide](AUTHORIZATION_GUIDE.md).

### Keycloak Admin Console Access

You can also access the Keycloak Admin Console directly for advanced user and realm management:

**Keycloak Admin Console:**
- **URL**: [http://localhost:9000](http://localhost:9000)
- **Username**: `admin` (from `KC_BOOTSTRAP_ADMIN_USERNAME` environment variable)
- **Password**: Check your `.env` or `.env.docker` file for `KC_BOOTSTRAP_ADMIN_PASSWORD`

**Default Keycloak Admin Credentials:**
```
Username: admin
Password: [Set via KC_BOOTSTRAP_ADMIN_PASSWORD environment variable]
```

**What you can do in Keycloak Admin Console:**
- Manage users and their roles
- Configure authentication settings
- View and modify realm settings
- Monitor user sessions
- Configure client settings

### Creating Additional Users And Sending API Requests

Once logged in as system admin, you can create additional users and other API requests in the system .

For example, to create a new user, you can use the following API request:

```bash
POST /api/user/create
Authorization: Bearer <your-access-token>
Content-Type: application/json

{
    "user_name": "john_doe",
    "first_name": "John",
    "last_name": "Doe", 
    "email": "john@example.com",
    "roles": ["user"]
}
```

For detailed API documentation, see [API.md](API.md) and [AUTHORIZATION_GUIDE.md](AUTHORIZATION_GUIDE.md).

---

## Usage

### Adding a New Microservice

1. Create a new directory for the microservice, e.g., `new_service`.
2. Add a `Dockerfile` and FastAPI app within `new_service`.
3. Update the `docker-compose.yml` to include the new service.
4. Add routing to the gateway app to forward requests to the new service.

### Keycloak Configuration

1. Access the Keycloak Admin Console at [http://localhost:9000](http://localhost:9000).
2. Get the Client Secret (if you want to use it for Keycloak API):

Go to your realm > Clients.

Click on the client you created (e.g., templateApp).

Go to the Credentials tab.

Copy the Client Secret shown in the interface.

![Client Secret](https://github.com/user-attachments/assets/aba6d6b9-c403-4a03-9b0b-f9ef6c188593)

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes and open a pull request.

---

## License

This project is licensed under the [MIT License](LICENSE).  
You are free to use, modify, and distribute this project in accordance with the terms of the license.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
- [Keycloak](https://www.keycloak.org/)

