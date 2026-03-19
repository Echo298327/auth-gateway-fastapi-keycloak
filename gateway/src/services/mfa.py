import httpx
from auth_gateway_serverkit.logger import init_logger
from auth_gateway_serverkit.keycloak.config import settings as kc_settings

logger = init_logger(__name__)

_mfa_client = httpx.AsyncClient(timeout=20)


async def validate_password(username: str, password: str) -> bool:
    """Validate password via the custom MFA auth endpoint."""
    url = f"{kc_settings.SERVER_URL}/realms/{kc_settings.REALM}/mfa/auth/validate"
    try:
        response = await _mfa_client.post(url, json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json().get("valid", False)
        return False
    except Exception as e:
        logger.error(f"Error validating password: {e}")
        return False


async def get_keycloak_uid_by_username(admin_token: str, username: str) -> str | None:
    """Look up a user's Keycloak UID by username via admin API."""
    url = f"{kc_settings.SERVER_URL}/admin/realms/{kc_settings.REALM}/users?username={username}&exact=true"
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        response = await _mfa_client.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]["id"]
        return None
    except Exception as e:
        logger.error(f"Error looking up user: {e}")
        return None


async def get_user_required_actions(admin_token: str, keycloak_uid: str) -> list:
    """Get a user's required actions from Keycloak."""
    url = f"{kc_settings.SERVER_URL}/admin/realms/{kc_settings.REALM}/users/{keycloak_uid}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        response = await _mfa_client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("requiredActions", [])
        return []
    except Exception as e:
        logger.error(f"Error getting required actions: {e}")
        return []


async def remove_required_action(admin_token: str, keycloak_uid: str, action: str) -> bool:
    """Remove a required action from a user in Keycloak."""
    url = f"{kc_settings.SERVER_URL}/admin/realms/{kc_settings.REALM}/users/{keycloak_uid}"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    try:
        current_actions = await get_user_required_actions(admin_token, keycloak_uid)
        updated_actions = [a for a in current_actions if a != action]
        response = await _mfa_client.put(url, headers=headers, json={"requiredActions": updated_actions})
        return response.status_code == 204
    except Exception as e:
        logger.error(f"Error removing required action: {e}")
        return False


async def enroll_mfa(keycloak_uid: str) -> dict | None:
    """Enroll a user in MFA via the custom Keycloak endpoint."""
    url = f"{kc_settings.SERVER_URL}/realms/{kc_settings.REALM}/mfa/totp/enroll"
    try:
        response = await _mfa_client.post(url, json={"userId": keycloak_uid})
        if response.status_code == 200:
            return response.json()
        logger.error(f"MFA enrollment failed: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error enrolling MFA: {e}")
        return None


async def verify_mfa_otp(keycloak_uid: str, otp: str) -> bool:
    """Verify an OTP code via the custom Keycloak endpoint."""
    url = f"{kc_settings.SERVER_URL}/realms/{kc_settings.REALM}/mfa/totp/verify"
    try:
        response = await _mfa_client.post(url, json={"userId": keycloak_uid, "otp": otp})
        if response.status_code == 200:
            return response.json().get("verified", False)
        return False
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return False
