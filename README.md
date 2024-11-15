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

## Getting Started

### Prerequisites

Make sure you have the following installed:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.10+](https://www.python.org/)
- Git CLI

---

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/repository-name.git
   cd repository-name
   ```

2. Copy the `.env.example` file to `.env` and configure it:

   ```bash
   cp .env.example .env
   ```

3. Start the services using Docker Compose:

   ```bash
   docker-compose up --build
   ```

4. Access the services:

   - **Gateway App:** [http://localhost:8080](http://localhost:8080)
   - **Keycloak Admin Console:** [http://localhost:9000](http://localhost:9000)

---

### Project Structure

```plaintext
.
│   .env
│   docker-compose.yml
│   LICENSE
│   README.md
│
├───.github
│   └───workflows
│           run-tests.yml
│
├───deployment
│   └───docker
│           gateway_dockerfile
│           users_dockerfile
│
├───gateway
│   │   requirements.txt
│   │
│   ├───src
│   │   │   app.py
│   │   │   config.py
│   │   │   logger.py
│   │   │   manager.py
│   │   │   requests.py
│   │   │   request_handler.py
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
    │   │   email_handler.py
    │   │   logger.py
    │   │   manager.py
    │   │   mongo_models.py
    │   │   password_gen.py
    │   │   request_handler.py
    │   │   schemas.py
    │   │   __init__.py
    │
    └───test
        │   test_manager.py
        │   __init__.py
```

---

### Environment Variables

Ensure your `.env` file includes the following variables:

```plaintext
# General
PROJECT_NAME=FastAPIStarter

# Gateway
GATEWAY_HOST=localhost
GATEWAY_PORT=8080

# User Manager
USER_MANAGER_HOST=localhost
USER_MANAGER_PORT=8001

# Keycloak
KEYCLOAK_URL=http://localhost:9000
REALM=your-realm-name
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
```

---

## Usage

### Adding a New Microservice

1. Create a new directory for the microservice, e.g., `new_service`.
2. Add a `Dockerfile` and FastAPI app within `new_service`.
3. Update the `docker-compose.yml` to include the new service.
4. Add routing to the gateway app to forward requests to the new service.

### Keycloak Configuration

1. Access the Keycloak Admin Console at [http://localhost:9000](http://localhost:9000).
2. Create a realm, client, and user roles as needed.
3. Update the `.env` file with the new configuration.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes and open a pull request.

---

## License

See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
- [Keycloak](https://www.keycloak.org/)

