# Serverkit & Keycloak Initializer Guide

## What is auth-gateway-serverkit?

[auth-gateway-serverkit](https://github.com/Echo298327/auth-gateway-serverkit) is a shared Python library used by both the **Gateway** and **IAM** services. It provides:

| Module | What it does |
|--------|-------------|
| `keycloak/initializer.py` | Full Keycloak initialization — realm, client, roles, policies, resources, permissions |
| `keycloak/client_api.py` | Low-level Keycloak REST API calls (tokens, resources, policies, permissions, user operations) |
| `keycloak/cleanup_api.py` | Deletes existing authorization config from Keycloak (permissions, policies, resources) |
| `keycloak/roles_api.py` | Keycloak realm role operations |
| `keycloak/user_api.py` | Keycloak user operations (create, get, update, delete) |
| `keycloak/config.py` | Keycloak settings loaded from environment variables |
| `keycloak/utils.py` | Utilities (dynamic permission naming) |
| `middleware/auth.py` | JWT authentication middleware |
| `middleware/rbac.py` | Role-based access control middleware |
| `http_client.py` | Shared async HTTP client |
| `logger.py` | Color-coded console logger |
| `email.py` | Email utilities |
| `password.py` | Password utilities |
| `string.py` | String utilities |

The package is published on [GitHub Releases](https://github.com/Echo298327/auth-gateway-serverkit/releases) and installed via `requirements.txt` in each service.

---

## Keycloak Initializer — How It Works

The entry point is `initialize_keycloak_server()` in `keycloak/initializer.py`. The IAM service calls it during startup (in `main.py`'s `lifespan`).

### Two Modes

| Mode | When | What happens |
|------|------|-------------|
| **Full init** (`cleanup_and_build=True`) | Config version changed | Connects, creates realm/client/roles, deletes all existing authz config, rebuilds everything from JSON |
| **Verify only** (`cleanup_and_build=False`) | Config version matches | Connects, gets admin token, returns immediately |

The mode is determined by comparing `KEYCLOAK_CONFIG_VERSION` in `iam/src/core/config.py` with the version stored in MongoDB's `service_versions` collection. See the [README — Keycloak Config Versioning](../README.md#keycloak-config-versioning) section.

### Full Initialization Flow (5 Phases)

#### Phase 1 — Connection Retry Loop

```
Attempt 1/30 → polls Keycloak SERVER_URL
Attempt 2/30 → waits 5 seconds, retries
...
Connected → proceeds
```

Keycloak takes 30-60+ seconds to start. The initializer retries up to **30 times** with a **5-second delay** between attempts (total ~2.5 minutes). This is normal — the IAM container starts before Keycloak is ready.

#### Phase 2 — Admin Token

Authenticates with Keycloak using `KC_BOOTSTRAP_ADMIN_USERNAME` / `KC_BOOTSTRAP_ADMIN_PASSWORD` to get an admin access token. All subsequent API calls use this token.

#### Phase 3 — Realm & Client Setup

Runs these steps sequentially (each depends on the previous):

| Step | Function | What it does |
|------|----------|-------------|
| 1 | `create_realm()` | Creates the realm (e.g. `templateRealm`) if it doesn't exist |
| 2 | `set_frontend_url()` | Sets `KEYCLOAK_FRONTEND_URL` on the realm |
| 3 | `create_client()` | Creates the OAuth2 client (e.g. `templateClient`) with authorization enabled |
| 4 | `create_realm_roles()` | Creates realm roles from `roles.json` (`user`, `admin`, `systemAdmin`) |
| 5 | `add_audience_protocol_mapper()` | Adds audience mapper so the client ID appears in JWT `aud` claim |
| 6 | `enable_edit_username()` | Enables username editing in the realm |

#### Phase 4 — Client UUID & Scope Cleanup

- Retrieves the client UUID (needed for authorization API calls)
- Removes unwanted default/optional OAuth2 scopes from the client

#### Phase 5 — Authorization Config (JSON-Driven)

Reads JSON config files from `iam/src/authorization/` (`roles.json` + `services/*.json`), cleans up all existing Keycloak authorization objects, and rebuilds them from scratch — resources, policies, and consolidated permissions.

For full details on the JSON format, how roles/policies/permissions work, and how to add new endpoints or services, see the [Authorization Guide](AUTHORIZATION_GUIDE.md).

---

## Customizing the Serverkit

You may need to modify `auth-gateway-serverkit` when you want to:

- Change how Keycloak initialization works (e.g. add new setup steps)
- Add new Keycloak API operations
- Modify the auth middleware behavior
- Add new shared utilities

There are two ways to work with the serverkit locally:

| | Option 1 — Add to `shared/` | Option 2 — Volume Mount |
|---|---|---|
| **How** | Clone into the project's `shared/` folder, change imports | Clone separately, mount into Docker via `docker-compose.dev.yml` |
| **Best for** | Full ownership, customizing the serverkit as part of your project | Temporary development / testing before publishing |
| **Imports** | Change to `from shared.auth_gateway_serverkit...` | Stay as `from auth_gateway_serverkit...` |
| **Docker** | Works with regular `docker compose up` | Needs `docker-compose.dev.yml` override |
| **Git** | Serverkit code lives inside your project | Serverkit stays a separate repo |

---

### Serverkit Package Structure

```
auth-gateway-serverkit/
├── pyproject.toml                  ← package metadata & version
├── setup.py                        ← legacy setup (mirrors pyproject.toml)
├── requirements.txt
└── src/
    └── auth_gateway_serverkit/
        ├── __init__.py
        ├── keycloak/
        │   ├── initializer.py      ← Keycloak bootstrap logic
        │   ├── client_api.py       ← REST API calls to Keycloak
        │   ├── cleanup_api.py      ← Authorization config cleanup
        │   ├── roles_api.py        ← Realm role operations
        │   ├── user_api.py         ← User operations
        │   ├── config.py           ← Keycloak env settings
        │   └── utils.py            ← Helpers
        ├── middleware/
        │   ├── auth.py             ← JWT validation
        │   ├── rbac.py             ← Role-based access control
        │   ├── config.py           ← Middleware settings
        │   ├── schemas.py          ← Middleware schemas
        │   └── fb_auth.py          ← Firebase auth
        ├── firebase/               ← Firebase integration
        ├── http_client.py
        ├── logger.py
        ├── email.py
        ├── password.py
        ├── string.py
        └── request_handler.py
```

---

### Option 1 — Add to `shared/` and Change Imports (Easier)

Use this when you want to fully own and customize the serverkit as part of your project. No volume mounts or separate repo needed.

> **Important:** If you choose this option, you are using your own copy of the serverkit. You no longer depend on the published `auth-gateway-serverkit` PyPI package — remove it from `requirements.txt` (see step 3). From this point on, you maintain the initializer, middleware, and all serverkit code yourself. Any future updates from the original repo need to be merged manually.

#### 1. Clone the Serverkit into `shared/`

```bash
cd auth-gateway-fastapi-keycloak

# Clone the serverkit source into the shared directory
git clone https://github.com/Echo298327/auth-gateway-serverkit.git temp-serverkit
```

Copy the package into `shared/`:

```bash
# Copy the package source
cp -r temp-serverkit/src/auth_gateway_serverkit shared/auth_gateway_serverkit

# Clean up
rm -rf temp-serverkit
```

Your project structure will look like:

```
auth-gateway-fastapi-keycloak/
├── shared/
│   ├── logging/                      ← existing shared logging
│   ├── auth_gateway_serverkit/       ← serverkit code (now local)
│   │   ├── keycloak/
│   │   ├── middleware/
│   │   ├── firebase/
│   │   └── ...
│   └── __init__.py
├── gateway/
├── iam/
└── ...
```

#### 2. Update Imports

Change all imports in the project from:

```python
from auth_gateway_serverkit.keycloak.initializer import initialize_keycloak_server
from auth_gateway_serverkit.middleware.auth import auth_middleware
from auth_gateway_serverkit.logger import init_logger
```

To:

```python
from shared.auth_gateway_serverkit.keycloak.initializer import initialize_keycloak_server
from shared.auth_gateway_serverkit.middleware.auth import auth_middleware
from shared.auth_gateway_serverkit.logger import init_logger
```

Also update the internal imports **inside** the serverkit itself — relative imports (e.g. `from ..logger import init_logger`) will continue to work, but any absolute imports within the serverkit that reference `auth_gateway_serverkit` need to be updated to `shared.auth_gateway_serverkit`.

#### 3. Remove the pip Dependency

The serverkit code now lives locally in `shared/` — you no longer need the published PyPI package.

Remove this line from **both** `gateway/requirements.txt` and `iam/requirements.txt`:

```
auth-gateway-serverkit==x.x.x   ← delete this line
```

The serverkit's own dependencies (e.g. `aiohttp`, `python-keycloak`, `PyJWT`) are still needed — make sure they remain in `requirements.txt`. You can find the full list in the serverkit's `pyproject.toml` under `[project] dependencies`.

#### 4. Run

No special Docker Compose override needed — just run as usual:

```bash
docker compose up --build -d
```

#### 5. Customize Freely

The serverkit code is now part of your project. You can edit any file in `shared/auth_gateway_serverkit/` directly — change the initializer, add new middleware, modify API calls — everything is under your control.

---

### Option 2 — Clone Separately + Docker Volume Mount

Use this when you want to develop the serverkit alongside the main project without publishing a new version for every change. The serverkit stays in its own repo.

#### 1. Clone both repositories

```bash
git clone https://github.com/Echo298327/auth-gateway-fastapi-keycloak.git
git clone https://github.com/Echo298327/auth-gateway-serverkit.git
```

Your directory should look like:

```
your-projects/
├── auth-gateway-fastapi-keycloak/    ← main project
└── auth-gateway-serverkit/           ← shared library
```

#### 2. Create `docker-compose.dev.yml`

In the main project root, create a `docker-compose.dev.yml` file:

```yaml
# Dev override: mount local serverkit into containers (no new package version needed).
#
# Usage:
#   docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
#   docker compose -f docker-compose.yml -f docker-compose.dev.yml down

services:
  gateway:
    volumes:
      - <SERVERKIT_PATH>/src/auth_gateway_serverkit:/usr/local/lib/python3.12/site-packages/auth_gateway_serverkit
  iam:
    volumes:
      - <SERVERKIT_PATH>/src/auth_gateway_serverkit:/usr/local/lib/python3.12/site-packages/auth_gateway_serverkit
```

Replace `<SERVERKIT_PATH>` with the **absolute path** to your cloned `auth-gateway-serverkit` directory.

Examples:
- **Windows**: `C:/Users/you/projects/auth-gateway-serverkit`
- **macOS/Linux**: `/home/you/projects/auth-gateway-serverkit`

> **Note:** Add `docker-compose.dev.yml` to `.gitignore` — the path is machine-specific and should not be committed.

#### 3. How It Works

The volume mount replaces the pip-installed `auth_gateway_serverkit` inside the container with your local source code. This means:

- Any change you make locally is immediately available in the running containers
- No version bump or package release needed
- Just restart the service to pick up changes

#### 4. Run

```bash
# Start with local serverkit
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# View logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f gateway iam

# Restart after making serverkit changes
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart gateway iam

# Stop
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

#### 5. When Done — Publish

When your changes are tested and ready:

1. Bump the version in `pyproject.toml` and `setup.py` in the serverkit repo
2. Commit, push, and create a new [GitHub release](https://github.com/Echo298327/auth-gateway-serverkit/releases)
3. Update `auth-gateway-serverkit==x.x.x` in `gateway/requirements.txt` and `iam/requirements.txt`
4. Run without the dev override: `docker compose up --build -d`
