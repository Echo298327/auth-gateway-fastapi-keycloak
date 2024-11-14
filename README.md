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

   - **Gateway App:** [http://localhost:8000](http://localhost:8000)
   - **Keycloak Admin Console:** [http://localhost:8080](http://localhost:8080)

---

### Project Structure

```plaintext
.
├── gateway
│   ├── app
│   │   ├── main.py           # Entry point for Gateway
│   │   ├── routers           # Route definitions
│   │   └── dependencies.py   # Dependency injections
│   └── Dockerfile
├── user_manager
│   ├── app
│   │   ├── main.py           # Entry point for User Manager
│   │   ├── models.py         # User models
│   │   └── routes.py         # Authentication routes
│   └── Dockerfile
├── keycloak
│   └── docker-compose.yml    # Keycloak service configuration
├── docker-compose.yml         # Main Docker Compose file
├── .env.example               # Example environment variables
├── README.md                  # Project documentation
└── .gitignore
```

---

### Environment Variables

Ensure your `.env` file includes the following variables:

```plaintext
# General
PROJECT_NAME=FastAPIStarter

# Gateway
GATEWAY_HOST=localhost
GATEWAY_PORT=8000

# User Manager
USER_MANAGER_HOST=localhost
USER_MANAGER_PORT=8001

# Keycloak
KEYCLOAK_URL=http://localhost:8080
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

1. Access the Keycloak Admin Console at [http://localhost:8080](http://localhost:8080).
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

