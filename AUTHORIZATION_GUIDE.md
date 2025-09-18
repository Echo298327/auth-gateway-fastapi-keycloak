# Authorization System Guide

## Overview

This FastAPI microservices project implements a comprehensive **Role-Based Access Control (RBAC)** system using **Keycloak** for authentication and authorization. The system follows a gateway pattern where all API requests are routed through a central gateway that validates permissions before forwarding requests to appropriate microservices.

## Architecture

```
Client Request
     ↓
[Gateway Service] ← JWT Token Validation & Permission Check
     ↓
[Microservice] ← Authorized Request with User Context
     ↓
[Database/Response]
```

### Key Components

1. **Gateway Service** (`gateway/`): Central API gateway that handles routing and authorization
2. **Users Service** (`users/`): Manages user data and operations
3. **Keycloak**: Identity and Access Management (IAM) server
4. **auth-gateway-serverkit**: Shared library for authentication middleware
5. **MongoDB**: Database for storing user information

## Authorization Flow

### 1. Authentication Flow
```
1. User sends credentials to /api/login
2. Gateway forwards to Keycloak for token generation
3. Keycloak validates credentials and returns JWT token
4. Gateway enriches response with user data from database
5. Client receives access token for subsequent requests
```

### 2. Request Authorization Flow
```
1. Client sends request with Bearer token in Authorization header
2. Gateway's @auth decorator validates JWT token with Keycloak
3. Middleware extracts user roles from token
4. System checks UMA (User Managed Access) permissions for specific resource
5. If authorized, request is forwarded to target microservice
6. Microservice receives request with user context in headers
```

## Role System

### Default Roles

The system defines three hierarchical roles:

#### 1. **user** (Basic Role)
- **Description**: Standard user with limited access
- **Permissions**: Can update own profile, view own data, get available roles
- **Default Role**: Assigned to new users

#### 2. **admin** (Administrative Role)
- **Description**: Administrator with elevated privileges
- **Permissions**: All user permissions + create/delete users
- **Use Case**: User management operations

#### 3. **systemAdmin** (Super Admin Role)
- **Description**: System administrator with full access
- **Permissions**: All admin permissions + system-level operations
- **Protection**: Cannot be modified or deleted by other users
- **Creation**: Automatically created during system initialization

### Role Hierarchy
```
systemAdmin (Full Access)
    ↓
admin (User Management)
    ↓
user (Basic Operations)
```

## Configuration Files

### 1. Global Role Configuration: `users/src/authorization/roles.json`

```json
{
  "realm_roles": [
    {
        "name": "user",
        "description": "Standard user with limited access"
    },
    {
        "name": "admin", 
        "description": "Administrator with elevated privileges"
    },
    {
        "name": "systemAdmin",
        "description": "System administrator with full access"
    }
  ],
  "policies": [
    {
      "name": "SystemAdmin-Access",
      "description": "Access restricted to system administrators",
      "roles": ["systemAdmin"]
    },
    {
      "name": "Administrators-Access", 
      "description": "Access restricted to admins and system administrators",
      "roles": ["admin", "systemAdmin"]
    },
    {
      "name": "Public-Access",
      "description": "Access available to all users", 
      "roles": ["user", "admin", "systemAdmin"]
    }
  ]
}
```

### 2. Service-Specific Permissions: `users/src/authorization/services/users.json`

```json
{
  "permissions": [
    {
      "name": "SystemAdmin",
      "description": "Permission for system administrators actions",
      "policies": ["SystemAdmin-Access"],
      "resources": ["user/get_by_keycloak_uid"]
    },
    {
      "name": "Administrators", 
      "description": "Permission for administrators actions",
      "policies": ["Administrators-Access"],
      "resources": ["user/create", "user/delete"]
    },
    {
      "name": "public",
      "description": "Permission for public actions", 
      "policies": ["Public-Access"],
      "resources": ["user/update", "user/get", "user/get_roles"]
    }
  ],
  "resources": [
    {
      "name": "user/create",
      "displayName": "Create User Endpoint",
      "url": "/api/user/create"
    },
    {
      "name": "user/update",
      "displayName": "Update User Endpoint", 
      "url": "/api/user/update"
    }
    // ... more resources
  ]
}
```

## How Authorization Works

### 1. JWT Token Validation

**File**: `auth-gateway-serverkit/src/auth_gateway_serverkit/middleware/auth.py`

```python
@auth(get_user_by_uid=get_by_keycloak_uid)
async def handle_request(request: Request, service: str, action: str):
    # 1. Extract Bearer token from Authorization header
    # 2. Validate JWT signature using Keycloak public key
    # 3. Extract user ID and roles from token payload
    # 4. Check UMA permissions for resource access
    # 5. Forward request if authorized
```

### 2. Permission Checking Process

1. **Resource Construction**: `service/action` (e.g., "user/create")
2. **UMA Token Request**: Send permission request to Keycloak
3. **Policy Evaluation**: Keycloak evaluates user roles against policies
4. **Authorization Decision**: Grant/deny access based on evaluation

### 3. User Context Injection

Authorized requests include user context in headers:
```python
headers = {"X-User": json.dumps(user)}
```

## Adding New Roles

### Step 1: Update Role Configuration

Edit `users/src/authorization/roles.json`:

```json
{
  "realm_roles": [
    // ... existing roles
    {
        "name": "moderator",
        "description": "Content moderator with specific privileges"
    }
  ],
  "policies": [
    // ... existing policies  
    {
      "name": "Moderator-Access",
      "description": "Access for moderators and above",
      "roles": ["moderator", "admin", "systemAdmin"]
    }
  ]
}
```

### Step 2: Update User Schema

Edit `users/src/schemas.py`:

```python
class AllowedRoles(str, Enum):
    user = "user"
    admin = "admin" 
    moderator = "moderator"  # Add new role
```

### Step 3: Restart Services

The role configuration is loaded during Keycloak initialization:
```bash
docker-compose down
docker-compose up --build
```

## Adding New API Endpoints with Authorization

### Step 1: Create the Endpoint

In your microservice (e.g., `users/src/app.py`):

```python
@app.post("/moderate_content")
async def moderate_content(
    data_errors: Tuple[ModerateContent, List[str]] = Depends(parse_request_body_to_model(ModerateContent)),
    user: Dict[str, Any] = Depends(get_request_user)
):
    return await handle_request(data_errors, manager.moderate_content, user)
```

### Step 2: Define Resource and Permission

Edit `users/src/authorization/services/users.json`:

```json
{
  "permissions": [
    // ... existing permissions
    {
      "name": "ContentModeration",
      "description": "Permission for content moderation", 
      "policies": ["Moderator-Access"],
      "resources": ["user/moderate_content"]
    }
  ],
  "resources": [
    // ... existing resources
    {
      "name": "user/moderate_content",
      "displayName": "Moderate Content Endpoint",
      "url": "/api/user/moderate_content" 
    }
  ]
}
```

### Step 3: Access via Gateway

The endpoint becomes available through the gateway:
```
POST /api/user/moderate_content
Authorization: Bearer <jwt_token>
```

## Adding New Microservices

### Step 1: Create Service Authorization Config

Create `users/src/authorization/services/new_service.json`:

```json
{
  "permissions": [
    {
      "name": "NewServiceAccess",
      "description": "Access to new service",
      "policies": ["Public-Access"], 
      "resources": ["new_service/endpoint1", "new_service/endpoint2"]
    }
  ],
  "resources": [
    {
      "name": "new_service/endpoint1",
      "displayName": "New Service Endpoint 1",
      "url": "/api/new_service/endpoint1"
    }
  ]
}
```

### Step 2: Update Gateway Service Map

Edit `gateway/src/config.py`:

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.SERVICE_MAP = {
        "user": self.USERS_URL,
        "new_service": self.NEW_SERVICE_URL,  # Add new service
    }
```

### Step 3: Implement Authentication in New Service

```python
from auth_gateway_serverkit.request_handler import get_request_user

@app.post("/endpoint1") 
async def endpoint1(user: Dict[str, Any] = Depends(get_request_user)):
    # User context is automatically injected
    # Access user data: user["id"], user["roles"], etc.
```

## Permission Management

### Understanding Policies

**Policies** define WHO can access resources based on roles:

- **SystemAdmin-Access**: Only systemAdmin role
- **Administrators-Access**: admin and systemAdmin roles  
- **Public-Access**: All authenticated users
- **Custom policies**: Define your own role combinations

### Understanding Permissions

**Permissions** define WHAT resources each policy can access:

- Map policies to specific API endpoints
- Support multiple resources per permission
- Enable fine-grained access control

### Understanding Resources

**Resources** represent individual API endpoints:

- Unique identifier (e.g., "user/create")
- Display name for admin interface
- URL pattern for routing

## Advanced Authorization Features

### 1. Dynamic Role Assignment

Users can have multiple roles simultaneously:

```python
# User with multiple roles
user_roles = ["user", "moderator"]

# Role checking in business logic
from users.src.utils import is_admins

if is_admins(user["roles"]):
    # User has admin or systemAdmin role
    pass
```

### 2. System Admin Protection

The system admin cannot be modified by other users:

```python
# In gateway/src/user_manager.py
async def check_unauthorized_access(request_data, user_id, path_segment):
    system_admin_id = await settings.get_system_admin_id()
    if (request_data.get("id") == system_admin_id or 
        path_segment == system_admin_id):
        if user_id != system_admin_id:
            return True  # Deny access
    return False
```

### 3. User Context Injection

All microservices receive user context:

```python
# In microservice endpoint
user = json.loads(request.headers.get("X-User", "{}"))
user_id = user.get("id")
user_roles = user.get("roles", [])
```

## Troubleshooting Authorization Issues

### 1. Token Validation Errors

**Problem**: `Invalid token` or `Token has expired`
**Solution**: 
- Check Keycloak server connectivity
- Verify client configuration
- Ensure token is not expired

### 2. Permission Denied Errors

**Problem**: `Access denied` (403 Forbidden)
**Solution**:
- Verify user has required role
- Check resource is properly configured
- Ensure policy includes user's role

### 3. Resource Not Found

**Problem**: `Service not found` (404 Not Found)  
**Solution**:
- Check service mapping in gateway config
- Verify resource exists in authorization config
- Ensure microservice is running

### 4. Role Assignment Issues

**Problem**: New roles not working
**Solution**:
- Restart services to reload configuration
- Check Keycloak admin console for role creation
- Verify user role assignment

## Security Best Practices

### 1. Token Management
- Use HTTPS in production
- Implement token refresh logic
- Set appropriate token expiration times

### 2. Role Design
- Follow principle of least privilege
- Use hierarchical role structure
- Regular permission audits

### 3. System Administration
- Protect system admin account
- Monitor administrative actions
- Implement role change logging

### 4. Resource Protection
- Validate all input data
- Implement rate limiting
- Use parameterized queries

## Monitoring and Logging

The system includes comprehensive logging:

```python
# Authentication events
logger.info(f"User {user_id} authenticated successfully")

# Authorization events  
logger.error(f"Access denied for user {user_id} to resource {resource}")

# Role management
logger.info(f"User {user_id} role updated to {new_roles}")
```

## Development Workflow

### 1. Local Development
```bash
# Start core services
docker-compose up postgres keycloak

# Run services locally for development
cd gateway && python src/main.py
cd users && python src/main.py
```

### 2. Testing Authorization
- Use Postman collection provided
- Test with different user roles
- Verify permission boundaries

### 3. Production Deployment
- Use `.env.docker` for container configuration
- Enable HTTPS/TLS
- Configure proper monitoring

## Conclusion

This authorization system provides:

- **Scalable Architecture**: Easy to add new services and endpoints
- **Fine-grained Control**: Role and resource-based permissions
- **Security**: JWT token validation and UMA authorization
- **Flexibility**: Configurable roles and policies
- **Maintainability**: Clear separation of concerns

The system is designed to grow with your application while maintaining security and performance standards. 