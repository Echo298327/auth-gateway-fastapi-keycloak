import os
import json
import asyncio
import aiohttp
from auth_gateway_serverkit.logger import init_logger
from config import settings


logger = init_logger("user.Keycloak_init")


async def check_keycloak_connection():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(settings.SERVER_URL) as response:
                if response.status == 200:
                    logger.info("Successfully connected to Keycloak server")
                    return True
                else:
                    logger.error(f"Failed to connect to Keycloak server. Status: {response.status}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to Keycloak server: {e}")
        return False


async def get_admin_token():
    url = f"{settings.SERVER_URL}/realms/master/protocol/openid-connect/token"
    payload = {
        'username': settings.KEYCLOAK_USER,
        'password': settings.KEYCLOAK_PASSWORD,
        'grant_type': 'password',
        'client_id': 'admin-cli'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['access_token']
                else:
                    logger.error(
                        f"Failed to get admin token. Status: {response.status}, Response: {await response.text()}"
                    )
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while getting admin token: {e}")
        return None


async def get_client_uuid(admin_token):
    url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients?clientId={settings.CLIENT_ID}"
    headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                clients = await response.json()
                if clients:
                    return clients[0]['id']  # UUID of the client
            logger.error(f"Failed to find client UUID for clientId '{settings.CLIENT_ID}'. Status: {response.status}")
            return None


async def get_resource_id(resource_name, admin_token, client_uuid):
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients/{client_uuid}/authz/resource-server/resource"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    resources = await response.json()
                    for resource in resources:
                        if resource['name'] == resource_name:
                            return resource['_id']
                else:
                    logger.error(f"Failed to fetch resources. Status: {response.status}, Response: {await response.text()}")
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while retrieving resource ID for '{resource_name}': {e}")
    return None


async def create_realm():
    admin_token = await get_admin_token()
    if not admin_token:
        return False

    url = f"{settings.SERVER_URL}/admin/realms"
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'realm': settings.REALM,
        'enabled': True,
        'accessTokenLifespan': 36000,  # Set token lifespan to 10 hours (in seconds)
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Realm '{settings.REALM}' created successfully")
                    return True
                elif response.status == 409:
                    logger.info(f"Realm '{settings.REALM}' already exists")
                    return True
                else:
                    logger.error(f"Failed to create realm. Status: {response.status}, Response: {await response.text()}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while creating realm: {e}")
        return False


async def create_client():
    admin_token = await get_admin_token()
    if not admin_token:
        return False

    url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients"
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'clientId': settings.CLIENT_ID,
        'name': settings.CLIENT_ID,
        'enabled': True,
        'publicClient': False,  # Must be False for Authorization Services
        'protocol': 'openid-connect',
        'redirectUris': ['*'],  # Update based on your app's requirements
        'webOrigins': ['*'],
        'directAccessGrantsEnabled': True,
        'serviceAccountsEnabled': True,  # REQUIRED for Authorization Services
        'standardFlowEnabled': True,
        'implicitFlowEnabled': False,
        'authorizationServicesEnabled': True,  # Enable Authorization Services
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Client '{settings.CLIENT_ID}' created successfully")
                    return True
                elif response.status == 409:
                    logger.info(f"Client '{settings.CLIENT_ID}' already exists")
                    return True
                else:
                    logger.error(f"Failed to create client. Status: {response.status}, Response: {await response.text()}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while creating client: {e}")
        return False


async def create_realm_roles():
    admin_token = await get_admin_token()
    if not admin_token:
        return False

    roles_to_create = [
        {'name': 'user', 'description': 'Standard user with limited access'},
        {'name': 'admin', 'description': 'Administrator with elevated privileges'},
        {'name': 'systemAdmin', 'description': 'System administrator with full access'}
    ]

    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }

    success = True
    for role in roles_to_create:
        url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/roles"
        payload = {
            'name': role['name'],
            'description': role['description'],
            'composite': False,
            'clientRole': False,
            'containerId': settings.REALM
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 201:
                        logger.info(f"Role '{role['name']}' created successfully in realm '{settings.REALM}'")
                    elif response.status == 409:
                        logger.info(f"Role '{role['name']}' already exists in realm '{settings.REALM}'")
                        # Optionally update the role description if it already exists
                        # await update_role_description(role['name'], role['description'], headers)
                    else:
                        logger.error(f"Failed to create role '{role['name']}'. Status: {response.status}, Response: {await response.text()}")
                        success = False
        except aiohttp.ClientError as e:
            logger.error(f"Connection error while creating role '{role['name']}': {e}")
            success = False

    return success


async def enable_edit_username():
    admin_token = await get_admin_token()
    if not admin_token:
        return False

    url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}"
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "realm": settings.REALM,
        "editUsernameAllowed": True  # Enable editing the username
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    logger.info(f"Enabled edit username for realm '{settings.REALM}' successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to enable edit username. Status: {response.status}, Response: {error_text}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while enabling edit username: {e}")
        return False


async def add_audience_protocol_mapper():
    admin_token = await get_admin_token()
    if not admin_token:
        return False

    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }

    # First, get the client ID (UUID) for your client
    url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients?clientId={settings.CLIENT_ID}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    clients = await response.json()
                    if clients:
                        client_uuid = clients[0]['id']
                    else:
                        logger.error(f"Client '{settings.CLIENT_ID}' not found")
                        return False
                else:
                    logger.error(f"Failed to retrieve client. Status: {response.status}, Response: {await response.text()}")
                    return False

            # Now, add the Protocol Mapper to the client
            url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients/{client_uuid}/protocol-mappers/models"
            payload = {
                "name": "audience",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-audience-mapper",
                "consentRequired": False,
                "config": {
                    "included.client.audience": settings.CLIENT_ID,
                    "id.token.claim": "true",
                    "access.token.claim": "true",
                    "claim.name": "aud",
                    "userinfo.token.claim": "false"
                }
            }
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Audience Protocol Mapper added successfully to client '{settings.CLIENT_ID}'")
                    return True
                elif response.status == 409:
                    logger.info(f"Audience Protocol Mapper already exists for client '{settings.CLIENT_ID}'")
                    return True
                else:
                    logger.error(f"Failed to add Audience Protocol Mapper. Status: {response.status}, Response: {await response.text()}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while adding Audience Protocol Mapper: {e}")
        return False


async def create_policy(policy_name, description, roles, admin_token, client_uuid):

    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients/{client_uuid}/authz/resource-server/policy/role"
    payload = {
        "name": policy_name,
        "description": description,
        "logic": "POSITIVE",
        "roles": [{"id": role} for role in roles]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Policy '{policy_name}' created successfully")
                elif response.status == 409:
                    logger.info(f"Policy '{policy_name}' already exists")
                else:
                    logger.error(f"Failed to create policy '{policy_name}'. Status: {response.status}, Response: {await response.text()}")
                return response.status == 201 or response.status == 409
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while creating policy '{policy_name}': {e}")
        return False


async def create_permission(permission_name, description, policies, resource_ids, admin_token, client_uuid):
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients/{client_uuid}/authz/resource-server/permission/resource"
    payload = {
        "name": permission_name,
        "description": description,
        "type": "resource",
        "resources": resource_ids,
        "policies": policies
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Permission '{permission_name}' created successfully")
                elif response.status == 409:
                    logger.info(f"Permission '{permission_name}' already exists")
                else:
                    logger.error(f"Failed to create permission '{permission_name}'. Status: {response.status}, Response: {await response.text()}")
                return response.status == 201 or response.status == 409
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while creating permission '{permission_name}': {e}")
        return False


async def create_resource(resource_name, display_name, url,admin_token, client_uuid):
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    resource_url = f"{settings.SERVER_URL}/admin/realms/{settings.REALM}/clients/{client_uuid}/authz/resource-server/resource"
    payload = {
        "owner": None,
        "name": resource_name,
        "displayName": display_name,
        "uri": url,
        "type": "REST API",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(resource_url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Resource '{resource_name}' created successfully")
                elif response.status == 409:
                    logger.info(f"Resource '{resource_name}' already exists")
                else:
                    logger.error(f"Failed to create resource '{resource_name}'. Status: {response.status}, Response: {await response.text()}")
                return response.status == 201 or response.status == 409
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while creating resource '{resource_name}': {e}")
        return False


async def process_json_config(admin_token, client_uuid):
    config_path = os.path.join(os.getcwd(), "keycloak_config.json")
    if not os.path.exists(config_path):
        logger.error("Configuration file not found")
        return False

    with open(config_path, 'r') as file:
        config = json.load(file)

    # Step 1: Create resources and collect their IDs
    resource_ids = {}
    for resource in config.get("resources", []):
        success = await create_resource(
            resource['name'],
            resource['displayName'],
            resource['url'],
            admin_token,
            client_uuid
        )
        if not success:
            logger.error(f"Failed to create resource: {resource['name']}")
            return False

        # Retrieve resource ID from Keycloak
        resource_id = await get_resource_id(resource['name'], admin_token, client_uuid)
        if resource_id:
            resource_ids[resource['name']] = resource_id
        else:
            logger.error(f"Failed to retrieve resource ID for: {resource['name']}")
            return False

    # Step 2: Create policies
    for policy in config.get("policies", []):
        success = await create_policy(
            policy['name'],
            policy['description'],
            policy['roles'],
            admin_token,
            client_uuid
        )
        if not success:
            logger.error(f"Failed to create policy: {policy['name']}")
            return False

    # Step 3: Create permissions and associate them with resources
    for permission in config.get("permissions", []):
        resource_names = permission.get('resources', [])
        if not resource_names:
            logger.error(f"No resources specified for permission '{permission['name']}'")
            return False

        # Get resource IDs for all associated resources
        resource_ids_list = [resource_ids.get(name) for name in resource_names]
        if None in resource_ids_list:
            missing_resources = [name for name, rid in zip(resource_names, resource_ids_list) if rid is None]
            logger.error(f"Missing resource IDs for: {missing_resources}")
            return False

        success = await create_permission(
            permission['name'],
            permission['description'],
            permission['policies'],
            resource_ids_list,  # Pass list of resource IDs
            admin_token,
            client_uuid
        )
        if not success:
            logger.error(f"Failed to create permission: {permission['name']}")
            return False

    return True


async def initialize_keycloak_server(max_retries=30, retry_delay=5):
    for attempt in range(max_retries):
        if await check_keycloak_connection():
            admin_token = await get_admin_token()
            if not admin_token:
                logger.error("Failed to get admin token")
                return False

            is_realm_created = await create_realm()
            if not is_realm_created:
                logger.error("Failed to create realm")
                return False

            is_client_created = await create_client()
            if not is_client_created:
                logger.error("Failed to create client")
                return False

            is_roles_created = await create_realm_roles()
            if not is_roles_created:
                logger.error("Failed to create realm roles")
                return False

            is_mapper_added = await add_audience_protocol_mapper()
            if not is_mapper_added:
                logger.error("Failed to add Audience Protocol Mapper")
                return False

            is_edit_username_enabled = await enable_edit_username()
            if not is_edit_username_enabled:
                logger.error("Failed to enable edit username")
                return False

            client_uuid = await get_client_uuid(admin_token)
            if not client_uuid:
                return False

            is_config_processed = await process_json_config(admin_token, client_uuid)
            if not is_config_processed:
                logger.error("Failed to process JSON configuration")
                return False

            logger.info("Keycloak initialization completed successfully")
            return True

        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed. Retrying in {retry_delay} seconds...")
        await asyncio.sleep(retry_delay)

    logger.error("Failed to initialize Keycloak after multiple attempts")
    return False
