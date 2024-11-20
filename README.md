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

## Postman Collection

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
   git clone https://github.com/your-username/repository-name.git
   cd repository-name
   ```

2. __Optional__ Copy the `.env.example` file to `.env` and configure it if you plan to run the services locally (without Docker Compose):
   <br> __Note:__ The .env file is not required for Docker Compose. It is used for running the services locally without containers.
   For Docker Compose, the environment variables are already handled within the docker-compose.yml file.

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
│   LICENSE
│   README.md
│   docker-compose.yml
│   keycloak-credentials.json
│   postman_collection.json
│
├───.github
│   └───workflows
│           run-tests.yml
│
├───deployment
│   │   pgadmin_server.json
│   │
│   └───docker
│           gateway_dockerfile
│           keycloak.conf
│           keycloak_dockerfile
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
    │   │   keycloak_init.py
    │   │   keycloak_manager.py
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

The `.env` file contains configuration for running the application.
* __Docker Compose:__ The default variables work seamlessly with the Docker Compose setup.
* __Local Development:__ If you want to run the services locally without Docker Compose, ensure you adjust the variables accordingly.




```plaintext
# MongoDB
CONNECTION_STRING=mongodb://localhost:27017
DB_NAME=templateApp

# APP Email
APP_EMAIL=
APP_PASSWORD=

# Keycloak server
KEYCLOAK_CREDENTIALS=../keycloak-credentials.json

# Gateway
GATEWAY_PORT=8080
GATEWAY_HOST=localhost
GATEWAY_URL=http://${GATEWAY_HOST}:${GATEWAY_PORT}

# Users
USERS_PORT=8081
USERS_HOST=localhost
USERS_URL=http://${USERS_HOST}:${USERS_PORT}
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

