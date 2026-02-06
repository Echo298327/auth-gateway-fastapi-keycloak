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
from auth_gateway_serverkit.keycloak.client_api import retrieve_client_token, refresh_client_token, revoke_client_token

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
            logger.error("Failed to get system admin ID")
            return False
        if (request_data.get("id") == system_admin_id or path_segment == system_admin_id or
                request_data.get("user_id") == system_admin_id):
            if user_id != system_admin_id:
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking unauthorized access: {str(e)}")
        return False


async def handle_login(login_data):
    try:
        return await retrieve_client_token(login_data.username, login_data.password)
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise


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
