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
- [API Documentation](API.md)
- [Postman Collection](postman_collection.json)
<br><br>You can use the Postman collection provided to test the API endpoints easily. Import the `postman_collection.json` file into Postman to get started.

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

## Usage

### Adding a New Microservice

1. Create a new directory for the microservice, e.g., `new_service`.
2. Add a `Dockerfile` and FastAPI app within `new_service`.
3. Update the `docker-compose.yml` to include the new service.
4. Add routing to the gateway app to forward requests to the new service.

### Keycloak Configuration

1. Access the Keycloak Admin Console at [http://localhost:9000](http://localhost:9000).
2. Get the Client Secret (for use in API requests like Postman):

Go to your realm > Clients.

Click on the client you created (e.g., templateApp).

Go to the Credentials tab.

Copy the Client Secret shown in the interface.

![Client Secret](https://github.com/user-attachments/assets/aba6d6b9-c403-4a03-9b0b-f9ef6c188593)

You’ll need this secret when using tools like Postman to get access tokens or authenticate your requests.

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

