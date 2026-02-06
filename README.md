# Auth Gateway — IAM, Authentication & Authorization

A complete **IAM (Identity & Access Management)** solution with **Keycloak**. Provides authentication, authorization, user management, role-based access control, and an API gateway — ready to plug into any project.

## What's Included

- **Gateway Service** — routes all API requests, validates JWT tokens, checks permissions via Keycloak
- **IAM Service** — user management (CRUD), role assignment, Keycloak initialization
- **Keycloak** — authentication, token issuing, role-based permission evaluation
- **MongoDB** — stores users, service versions
- **PostgreSQL** — Keycloak's database
- **PgAdmin** — PostgreSQL admin UI
- **auth-gateway-serverkit** — shared library for auth middleware, Keycloak API, request handling
- **Configurable RBAC** — define roles, policies, and per-endpoint permissions in JSON files
- **CI/CD Pipeline** — linting, security scanning, and tests on pull requests

## Documentation

- [API Documentation](API.md) — all endpoint references
- [Authorization Guide](AUTHORIZATION_GUIDE.md) — how roles, policies, and permissions work; how to add new roles/endpoints/services
- [Serverkit & Initializer Guide](SERVERKIT_GUIDE.md) — how the Keycloak initializer works, customizing the serverkit, local dev without publishing
- [Postman Collection](postman_collection.json) — import into Postman to test all endpoints

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.12+](https://www.python.org/)
- [MongoDB](https://www.mongodb.com/) (running locally or cloud-hosted)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Echo298327/auth-gateway-fastapi-keycloak.git
   cd auth-gateway-fastapi-keycloak
   ```

2. Configure environment variables:
   - `.env.docker` — used by Docker Compose (pre-configured, works out of the box)
   - `.env` — used for local development without Docker

3. Start all services:

   ```bash
   docker compose up --build -d
   ```

4. Access the services:

   | Service | URL |
   |---------|-----|
   | Gateway | http://localhost:8080 |
   | IAM | http://localhost:8081 |
   | Keycloak Admin Console | http://localhost:9000 |
   | PgAdmin | http://localhost:5050 |

### First Login

A system admin account is created automatically on first startup.

```
POST http://localhost:8080/api/login
Body: {
  "username": "sysadmin",
  "password": "<SYSTEM_ADMIN_PASSWORD from .env.docker>"
}
```

The response contains `access_token`, `refresh_token`, and user data. Use the access token in the `Authorization: Bearer <token>` header for all subsequent requests.

### Postman

1. Import `postman_collection.json` into Postman
2. Run the Login request
3. The token is automatically saved to the environment
4. All other requests use it automatically

---

## Project Structure

```
auth-gateway-fastapi-keycloak/
|
|-- .env                              # Local dev environment variables
|-- .env.docker                       # Docker environment variables
|-- docker-compose.yml                # All services orchestration
|-- API.md                            # API endpoint reference
|-- AUTHORIZATION_GUIDE.md            # Role & permission guide
|-- postman_collection.json           # Postman collection
|
|-- deployment/
|   |-- docker/
|   |   |-- gateway_dockerfile
|   |   |-- iam_dockerfile
|   |   |-- keycloak_dockerfile
|   |   |-- keycloak.conf
|   |-- pgadmin_server.json
|
|-- shared/                           # Shared utilities across services
|   |-- logging/
|       |-- log_header.py
|
|-- gateway/                          # Gateway Service
|   |-- requirements.txt
|   |-- src/
|       |-- main.py
|       |-- api/routes/
|       |   |-- gateway.py            # Routes: login, refresh, logout, proxy
|       |-- core/
|       |   |-- config.py             # Service map, app settings
|       |-- schemas/
|       |   |-- gateway.py            # Login, Refresh request models
|       |-- services/
|           |-- manager.py            # Request forwarding, auth handlers
|
|-- iam/                              # IAM Service (Identity & Access Management)
|   |-- requirements.txt
|   |-- src/
|       |-- main.py                   # Startup: DB init, Keycloak init, admin creation
|       |-- api/routes/
|       |   |-- user.py               # User CRUD endpoints
|       |-- authorization/            # Role & permission config (JSON)
|       |   |-- roles.json            # Realm roles + policies
|       |   |-- services/
|       |       |-- iam.json          # Resources + permissions for IAM
|       |-- core/
|       |   |-- config.py             # DB, Keycloak, app settings
|       |-- domains/
|       |   |-- users/                # User domain
|       |   |   |-- models/user.py    # Beanie document model
|       |   |   |-- schemas/user.py   # Pydantic schemas + AllowedRoles
|       |   |   |-- services/user_manager.py
|       |   |   |-- db/mongo/user.py  # DB operations
|       |   |-- service_versions/     # Config version tracking
|       |   |   |-- models/service_version.py
|       |   |   |-- db/mongo/service_version.py
|       |   |-- organizations/        # Placeholder for future domain
|       |   |-- licenses/             # Placeholder for future domain
|       |-- utils/
|           |-- admin.py              # System admin helpers
|           |-- roles.py              # Role validation
|           |-- validation.py         # Input validation
|           |-- exception_handler.py
```

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8080 | API gateway, JWT validation, permission checks, request routing |
| IAM | 8081 | User management, Keycloak initialization, role management |
| Keycloak | 9000 | Identity provider, token issuer, authorization server |
| PostgreSQL | 5432 | Keycloak database |
| PgAdmin | 5050 | PostgreSQL admin interface |

---

## Role System

Three default roles: `user`, `admin`, `systemAdmin`.

- Users can have **multiple roles** at the same time
- Roles are assigned when creating a user and can be changed via update
- `systemAdmin` is created automatically and cannot be assigned through the API
- Roles, policies, and permissions are defined in JSON files under `iam/src/authorization/`

For full details on how to add roles, restrict endpoints, and add new services, see the [Authorization Guide](AUTHORIZATION_GUIDE.md).

---

## Keycloak Config Versioning

The IAM service tracks a `KEYCLOAK_CONFIG_VERSION` in code. On startup it compares with the version stored in MongoDB:

- **Different**: runs full Keycloak sync (delete + recreate roles, policies, resources, permissions)
- **Same**: skips, only verifies connection

Bump the version in `iam/src/core/config.py` whenever you change `roles.json` or any file in `authorization/services/`.

---

## Keycloak Admin Console

For advanced management you can access Keycloak directly:

- **URL**: http://localhost:9000
- **Username**: `admin` (from `KC_BOOTSTRAP_ADMIN_USERNAME`)
- **Password**: from `KC_BOOTSTRAP_ADMIN_PASSWORD` in `.env.docker`

---

## CI/CD Pipeline

Runs automatically on pull requests to `main`:

| Check | Description |
|-------|-------------|
| Lint | Flake8 (unused imports, variables) |
| Security (Dependencies) | Trivy vulnerability scan |
| Security (Docker) | Trivy Docker image scan |
| Tests | pytest |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT License](LICENSE)
