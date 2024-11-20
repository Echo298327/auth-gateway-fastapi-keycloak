import httpx
import json
import aiohttp

try:
    from config import settings
    from logger import init_logger
except ImportError:
    from .logger import init_logger
    from .config import settings

logger = init_logger("users.Keycloak_manager")


async def retrieve_token(username, password):
    with open(settings.KEYCLOAK_CREDENTIALS, 'r') as file:
        keycloak_credentials = json.load(file)

    client_id = keycloak_credentials.get('client_id')
    client_secret = keycloak_credentials.get('client_secret')
    realm = keycloak_credentials.get('realm')
    server_url = keycloak_credentials.get('server_url')
    scope = "openid"
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        url = f"{server_url}/realms/{realm}/protocol/openid-connect/token"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, data=body, headers=headers)
            if response.status_code == 200:
                token = response.json().get('access_token')
                return token
            else:
                logger.error(f"Error retrieving token: {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error retrieving token: {e}")
        return None


async def get_admin_token():
    with open(settings.KEYCLOAK_CREDENTIALS, 'r') as file:
        keycloak_credentials = json.load(file)

    keycloak_url = keycloak_credentials['server_url']
    admin_username = keycloak_credentials['admin_u']
    admin_password = keycloak_credentials['admin_p']
    url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
    payload = {
        'username': admin_username,
        'password': admin_password,
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
                    logger.error(f"Failed to get admin token. Status: {response.status}, Response: {await response.text()}")
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while getting admin token: {e}")
        return None


async def add_user_to_keycloak(user_name, first_name, last_name, email: str, password: str):
    with open(settings.KEYCLOAK_CREDENTIALS, 'r') as file:
        keycloak_credentials = json.load(file)

    realm = keycloak_credentials.get('realm')
    server_url = keycloak_credentials.get('server_url')
    try:
        token = await get_admin_token()
        if not token:
            return {'status': 'error', 'message': "Error creating user in keycloak"}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        body = {
                "username": user_name,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "totp": False,
                "emailVerified": True,
                "email": email,
                "disableableCredentialTypes": [],
                "requiredActions": [],
                "notBefore": 0,
                "access": {
                    "manageGroupMembership": True,
                    "view": True,
                    "mapRoles": True,
                    "impersonate": True,
                    "manage": True
                },
                "credentials": [{"type": "password", "value": password, "temporary": False}]
                }
        url = f"{server_url}/admin/realms/{realm}/users"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=body, headers=headers)
            if response.status_code == 201:
                location_header = response.headers.get('Location')
                user_uuid = location_header.rstrip('/').split('/')[-1]
                return {'status': 'success', 'keycloakUserId': user_uuid}
            else:
                logger.error(f"Error creating user in keycloak: {response.text}, response status: {response.status_code}")
                return {'status': 'error', 'message': "Error creating user in keycloak", "keycloakUserId": None}
    except Exception as e:
        logger.error(f"Error creating user in keycloak: {e}")
        return {'status': 'error', 'message': "Error creating user in keycloak"}


async def update_user_in_keycloak(user_id, user_name, first_name, last_name, email):
    try:
        with open(settings.KEYCLOAK_CREDENTIALS, 'r') as file:
            keycloak_credentials = json.load(file)

        server_url = keycloak_credentials.get('server_url')
        realm = keycloak_credentials.get('realm')

        token = await get_admin_token()
        if not token:
            return {'status': 'error', 'message': "Error updating user in keycloak"}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        body = {
            "username": user_name,
            "firstName": first_name,
            "lastName": last_name,
            "email": email
        }
        url = f"{server_url}/admin/realms/{realm}/users/{user_id}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.put(url, json=body, headers=headers)
            if response.status_code == 204:
                return {'status': 'success'}
            else:
                logger.error(f"Error updating user in keycloak: {response.text}")
                return {'status': 'error', 'message': "Error updating user in keycloak"}
    except Exception as e:
        logger.error(f"Error updating user in keycloak: {e}")
        return {'status': 'error', 'message': "Error updating user in keycloak"}


async def delete_user_from_keycloak(user_id):
    try:
        with open(settings.KEYCLOAK_CREDENTIALS, 'r') as file:
            keycloak_credentials = json.load(file)

        server_url = keycloak_credentials.get('server_url')
        realm = keycloak_credentials.get('realm')

        token = await get_admin_token()
        if not token:
            return {'status': 'error', 'message': "Error deleting user from keycloak"}
        headers = {
            "Authorization": f"Bearer {token}"
        }
        url = f"{server_url}/admin/realms/{realm}/users/{user_id}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.delete(url, headers=headers)
            if response.status_code == 204:
                return {'status': 'success'}
            else:
                logger.error(f"Error deleting user from keycloak: {response.text}")
                return {'status': 'error', 'message': "Error deleting user from keycloak"}
    except Exception as e:
        logger.error(f"Error deleting user from keycloak: {e}")
        return {'status': 'error', 'message': "Error deleting user from keycloak"}