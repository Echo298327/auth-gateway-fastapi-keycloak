import datetime
import httpx
from fastapi import Request, status
from auth_gateway_serverkit.logger import init_logger
import auth_gateway_serverkit.http_client as http
from typing import Union, Dict, List, Any
from config import settings
from starlette.datastructures import UploadFile as StarletteUploadFile
from auth_gateway_serverkit.request_handler import parse_request


logger = init_logger("gateway.manager")


async def process_request(
        service: Union[str, None] = None,
        action: Union[str, None] = None,
        request: Union[Request, None] = None,
        path: Union[str, None] = None
):
    # Determine content type and parse accordingly
    request_data, content_type = await parse_request(request)
    user_roles = request.state.realm_roles

    # Construct the URL path, including additional path segments if any
    path_segment = f"/{path}" if path else ""
    url = f"{settings.SERVICE_MAP.get(service)}/{action}{path_segment}"

    # Check for invalid service mapping
    if 'None' in url:
        return {
            "message": "Service not found",
            "status_code": status.HTTP_404_NOT_FOUND
        }

    logger.info(f"Forwarding request to: {url}")
    return await forward_request_and_process_response(
        url,
        request.method,
        content_type,
        request_data,
        user_roles
    )


async def forward_request_and_process_response(
    url: str,
    method: str,
    content_type: str,
    request_data: Dict[str, Any],
    roles: List[str]
) -> Dict[str, Any]:
    try:
        start_time = datetime.datetime.now()
        method = method.upper()
        response = None

        headers = {"X-Roles": ",".join(roles) if roles else ""}

        # Handle different HTTP methods
        if method in ["POST", "PUT"]:
            if content_type == "json":
                response = await http.post(url, json=request_data, headers=headers, timeout=150) if method == "POST" else \
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
                response = await http.post(url, data=data, files=files, headers=headers, timeout=150) if method == "POST" else \
                    await http.put(url, data=data, files=files, timeout=150)
            else:
                response = await http.post(url, data=request_data, headers=headers, timeout=150) if method == "POST" else \
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
