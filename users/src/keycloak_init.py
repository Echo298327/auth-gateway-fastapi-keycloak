import json
import asyncio
import time

import aiohttp
from logger import init_logger
from config import settings


logger = init_logger("user.Keycloak_init")
with open(settings.KEYCLOAK_CREDENTIALS, 'r') as file:
    keycloak_config = json.load(file)
    file.close()

KEYCLOAK_URL = keycloak_config['server_url']
KEYCLOAK_REALM = keycloak_config['realm']
CLIENT_ID = keycloak_config['client_id']
ADMIN_USERNAME = keycloak_config['admin_u']
ADMIN_PASSWORD = keycloak_config['admin_p']


async def check_keycloak_connection():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(KEYCLOAK_URL) as response:
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
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    payload = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD,
        'grant_type': 'password',
        'client_id': 'admin-cli'
    }
    logger.info(f"Sending request to {url}")
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


async def create_realm():
    admin_token = await get_admin_token()
    if not admin_token:
        return False

    url = f"{KEYCLOAK_URL}/admin/realms"
    logger.info(f"Sending request to {url}")
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'realm': KEYCLOAK_REALM,
        'enabled': True,
        'accessTokenLifespan': 36000,  # Set token lifespan to 10 hours (in seconds)
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Realm '{KEYCLOAK_REALM}' created successfully")
                    return True
                elif response.status == 409:
                    logger.info(f"Realm '{KEYCLOAK_REALM}' already exists")
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

    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients"
    logger.info(f"Sending request to {url}")
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'clientId': CLIENT_ID,
        'name': CLIENT_ID,
        'enabled': True,
        'publicClient': True,  # Set to False if you are using 'client_secret' to authenticate
        'protocol': 'openid-connect',
        'redirectUris': ['*'],  # Redirect URIs for the client
        'webOrigins': ['*'],
        'directAccessGrantsEnabled': True,  # Enables password grant type
        'serviceAccountsEnabled': False,  # Only needed if you want to use service accounts
        'standardFlowEnabled': True,  # Enable standard OpenID Connect flows (e.g., auth code)
        'implicitFlowEnabled': False,  # Set to True if you need implicit flow
        'authorizationServicesEnabled': False,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Client '{CLIENT_ID}' created successfully")
                    return True
                elif response.status == 409:
                    logger.info(f"Client '{CLIENT_ID}' already exists")
                    return True
                else:
                    logger.error(f"Failed to create client. Status: {response.status}, Response: {await response.text()}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Connection error while creating client: {e}")
        return False


async def initialize_keycloak_server(max_retries=30, retry_delay=5):
    # wait for Keycloak server to start
    for attempt in range(max_retries):
        if await check_keycloak_connection():
            is_realm_created = await create_realm()
            if not is_realm_created:
                logger.error("Failed to create realm")
                return False
            is_client_created = await create_client()
            if not is_client_created:
                logger.error("Failed to create client")
                return False
            return True
        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed. Retrying in {retry_delay} seconds...")
        await asyncio.sleep(retry_delay)

    logger.error("Failed to initialize Keycloak after multiple attempts")
    return False
