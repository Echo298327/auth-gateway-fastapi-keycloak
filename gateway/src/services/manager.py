import datetime
import httpx
import json
from fastapi import Request, status
import auth_gateway_serverkit.http_client as http
from typing import Union, Dict, Any
from core.config import settings
from starlette.datastructures import UploadFile as StarletteUploadFile
from auth_gateway_serverkit.request_handler import parse_request
from auth_gateway_serverkit.logger import init_logger
from auth_gateway_serverkit.keycloak.client import retrieve_client_token, refresh_client_token, revoke_client_token, get_admin_token
from auth_gateway_serverkit.keycloak.config import settings as kc_settings

logger = init_logger("gateway.manager")


async def process_request(
        service: Union[str, None] = None,
        action: Union[str, None] = None,
        request: Union[Request, None] = None,
        path: Union[str, None] = None
):
    # Determine content type and parse accordingly
    request_data, content_type = await parse_request(request)
    user = request.state.user

    # Construct the URL path, including additional path segments if any
    path_segment = f"/{path}" if path else ""
    url = f"{settings.SERVICE_MAP.get(service)}/{action}{path_segment}"

    # Check for invalid service mapping
    if 'None' in url:
        return {
            "message": "Service not found",
            "status_code": status.HTTP_404_NOT_FOUND
        }

    # check if user try to access/modify system admin details
    if await check_unauthorized_access(request_data, user.get("id"), path_segment[1:]):
        return {
            "message": "Access denied",
            "status_code": status.HTTP_403_FORBIDDEN
        }

    logger.info(f"Forwarding request to: {url}")
    return await forward_request_and_process_response(
        url,
        request.method,
        content_type,
        request_data,
        user
    )


async def forward_request_and_process_response(
        url: str,
        method: str,
        content_type: str,
        request_data: Dict[str, Any],
        user: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        start_time = datetime.datetime.now()
        method = method.upper()
        response = None
        # Add the user information to the headers
        headers = {"X-User": json.dumps(user)}

        # Handle different HTTP methods
        if method in ["POST", "PUT"]:
            if content_type == "json":
                response = await http.post(url, json=request_data, headers=headers,
                                           timeout=150) if method == "POST" else \
                    await http.put(url, json=request_data, headers=headers, timeout=150)
            elif content_type == "multipart":
                files = {
                    key: (file.filename, file.file, file.content_type)
                    for key, file in request_data.items()
                    if isinstance(file, StarletteUploadFile)
                }
                data = {
                    key: str(value)
                    for key, value in request_data.items()
                    if not isinstance(value, StarletteUploadFile)
                }
                response = await http.post(url, data=data, files=files, headers=headers,
                                           timeout=150) if method == "POST" else \
                    await http.put(url, data=data, files=files, timeout=150)
            else:
                response = await http.post(url, data=request_data, headers=headers,
                                           timeout=150) if method == "POST" else \
                    await http.put(url, data=request_data, headers=headers, timeout=150)
        elif method == "GET":
            response = await http.get(url, params=request_data, headers=headers, timeout=150)
        elif method == "DELETE":
            response = await http.delete(url, params=request_data, headers=headers, timeout=150)
        else:
            return {
                "message": "Method not supported",
                "status_code": status.HTTP_405_METHOD_NOT_ALLOWED
            }

        end_time = datetime.datetime.now()
        logger.info(
            f"Time taken: {end_time - start_time}. "
            f"Response status: {response.get('status_code')}"
        )
        return response

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text} - URL: {url}")
        return {
            "message": f"HTTP error: {e.response.status_code}",
            "status_code": e.response.status_code
        }
    except Exception as e:
        logger.error(f"Error forwarding {method} request to {url}: {str(e)}")
        return {
            "message": f"Internal Server Error: {str(e)}",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }


async def get_by_keycloak_uid(uid):
    try:
        url = f"{settings.SERVICE_MAP.get('user')}/get_by_keycloak_uid/{uid}"
        response = await http.get(url)
        if "data" in response:
            return response["data"]
        return None
    except Exception as e:
        logger.error(f"Request error: {e}")
        return None


async def check_unauthorized_access(request_data, user_id, path_segment):
    try:
        system_admin_id = await settings.get_system_admin_id()
        if not system_admin_id:
            logger.error("Failed to get system admin ID, denying access")
            return True
        if (request_data.get("id") == system_admin_id or path_segment == system_admin_id or
                request_data.get("user_id") == system_admin_id):
            if user_id != system_admin_id:
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking unauthorized access: {str(e)}")
        return True


async def handle_login(login_data):
    """
    Handle login with MFA support.

    Flow:
    1. Try Keycloak login (with totp if provided)
    2. If 200 -> return token response
    3. If "not fully set up" -> CONFIGURE_TOTP required action
       - No totp: enroll user, return QR code
       - With totp: verify OTP, remove required action, return setup_complete
    4. If login failed without totp -> validate password separately
       - Password valid -> user needs OTP -> return mfa_required
       - Password invalid -> return the original Keycloak error
    """
    try:
        response = await retrieve_client_token(login_data.username, login_data.password, login_data.totp)

        if response is None:
            return {"error": True, "message": "Authentication service unavailable", "status_code": status.HTTP_503_SERVICE_UNAVAILABLE}

        if response.status_code == 200:
            return response

        error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        error_description = error_data.get("error_description", "")

        if "not fully set up" in error_description.lower():
            return await _handle_account_not_setup(login_data)

        if login_data.totp is None and response.status_code == 401:
            password_valid = await _validate_password(login_data.username, login_data.password)
            if password_valid:
                return {"mfa_required": True, "mfa_action": "verify", "message": "OTP code required"}

        return response

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise


async def _handle_account_not_setup(login_data):
    """Handle CONFIGURE_TOTP required action flow."""
    admin_token = await get_admin_token()
    if not admin_token:
        return {"error": True, "message": "Authentication service error", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}

    keycloak_uid = await _get_keycloak_uid_by_username(admin_token, login_data.username)
    if not keycloak_uid:
        return {"error": True, "message": "User not found", "status_code": status.HTTP_404_NOT_FOUND}

    required_actions = await _get_user_required_actions(admin_token, keycloak_uid)

    if "CONFIGURE_TOTP" not in required_actions:
        return {"error": True, "message": f"Account setup required: {', '.join(required_actions)}", "status_code": status.HTTP_400_BAD_REQUEST}

    if login_data.totp:
        verified = await _verify_mfa_otp(keycloak_uid, login_data.totp)
        if not verified:
            return {"error": True, "message": "Invalid OTP code", "status_code": status.HTTP_400_BAD_REQUEST}
        await _remove_required_action(admin_token, keycloak_uid, "CONFIGURE_TOTP")
        return {"mfa_required": True, "mfa_action": "setup_complete", "message": "MFA setup complete. Please login again with your OTP code."}

    qr_data = await _enroll_mfa(keycloak_uid)
    if not qr_data:
        return {"error": True, "message": "Failed to generate QR code", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}

    return {"mfa_required": True, "mfa_action": "setup", "qr_code": qr_data.get("qrCodeDataUrl"), "message": "Scan QR code with your authenticator app"}


async def _validate_password(username: str, password: str) -> bool:
    """Validate password via the custom MFA auth endpoint."""
    url = f"{kc_settings.SERVER_URL}/realms/{kc_settings.REALM}/mfa/auth/validate"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json={"username": username, "password": password})
            if response.status_code == 200:
                return response.json().get("valid", False)
            return False
    except Exception as e:
        logger.error(f"Error validating password: {e}")
        return False


async def _get_keycloak_uid_by_username(admin_token: str, username: str) -> str | None:
    """Look up a user's Keycloak UID by username via admin API."""
    url = f"{kc_settings.SERVER_URL}/admin/realms/{kc_settings.REALM}/users?username={username}&exact=true"
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                users = response.json()
                if users:
                    return users[0]["id"]
            return None
    except Exception as e:
        logger.error(f"Error looking up user: {e}")
        return None


async def _get_user_required_actions(admin_token: str, keycloak_uid: str) -> list:
    """Get a user's required actions from Keycloak."""
    url = f"{kc_settings.SERVER_URL}/admin/realms/{kc_settings.REALM}/users/{keycloak_uid}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("requiredActions", [])
            return []
    except Exception as e:
        logger.error(f"Error getting required actions: {e}")
        return []


async def _remove_required_action(admin_token: str, keycloak_uid: str, action: str) -> bool:
    """Remove a required action from a user in Keycloak."""
    url = f"{kc_settings.SERVER_URL}/admin/realms/{kc_settings.REALM}/users/{keycloak_uid}"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    try:
        current_actions = await _get_user_required_actions(admin_token, keycloak_uid)
        updated_actions = [a for a in current_actions if a != action]
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.put(url, headers=headers, json={"requiredActions": updated_actions})
            return response.status_code == 204
    except Exception as e:
        logger.error(f"Error removing required action: {e}")
        return False


async def _enroll_mfa(keycloak_uid: str) -> dict | None:
    """Enroll a user in MFA via the custom Keycloak endpoint."""
    url = f"{kc_settings.SERVER_URL}/realms/{kc_settings.REALM}/mfa/totp/enroll"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json={"userId": keycloak_uid})
            if response.status_code == 200:
                return response.json()
            logger.error(f"MFA enrollment failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error enrolling MFA: {e}")
        return None


async def _verify_mfa_otp(keycloak_uid: str, otp: str) -> bool:
    """Verify an OTP code via the custom Keycloak endpoint."""
    url = f"{kc_settings.SERVER_URL}/realms/{kc_settings.REALM}/mfa/totp/verify"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json={"userId": keycloak_uid, "otp": otp})
            if response.status_code == 200:
                return response.json().get("verified", False)
            return False
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return False


async def handle_refresh(refresh_token: str):
    try:
        return await refresh_client_token(refresh_token)
    except Exception as e:
        logger.error(f"Error during refresh: {str(e)}")
        raise


async def handle_logout(refresh_token: str):
    try:
        return await revoke_client_token(refresh_token)
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise
