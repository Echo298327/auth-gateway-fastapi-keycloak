from fastapi import status
from auth_gateway_serverkit.logger import init_logger
from auth_gateway_serverkit.keycloak.client import retrieve_client_token, refresh_client_token, revoke_client_token, get_admin_token
from services.mfa import (
    validate_password,
    get_keycloak_uid_by_username,
    get_user_required_actions,
    remove_required_action,
    enroll_mfa,
    verify_mfa_otp,
)

logger = init_logger(__name__)


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
            password_valid = await validate_password(login_data.username, login_data.password)
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

    keycloak_uid = await get_keycloak_uid_by_username(admin_token, login_data.username)
    if not keycloak_uid:
        return {"error": True, "message": "User not found", "status_code": status.HTTP_404_NOT_FOUND}

    required_actions = await get_user_required_actions(admin_token, keycloak_uid)

    if "CONFIGURE_TOTP" not in required_actions:
        return {"error": True, "message": f"Account setup required: {', '.join(required_actions)}", "status_code": status.HTTP_400_BAD_REQUEST}

    if login_data.totp:
        verified = await verify_mfa_otp(keycloak_uid, login_data.totp)
        if not verified:
            return {"error": True, "message": "Invalid OTP code", "status_code": status.HTTP_400_BAD_REQUEST}
        await remove_required_action(admin_token, keycloak_uid, "CONFIGURE_TOTP")
        return {"mfa_required": True, "mfa_action": "setup_complete", "message": "MFA setup complete. Please login again with your OTP code."}

    qr_data = await enroll_mfa(keycloak_uid)
    if not qr_data:
        return {"error": True, "message": "Failed to generate QR code", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}

    return {"mfa_required": True, "mfa_action": "setup", "qr_code": qr_data.get("qrCodeDataUrl"), "message": "Scan QR code with your authenticator app"}


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
