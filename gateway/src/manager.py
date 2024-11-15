import datetime
from fastapi import Request, status
from logger import init_logger
from typing import Union, Dict, Any
from config import settings
from requests import post
from starlette.datastructures import UploadFile as StarletteUploadFile
from request_handler import parse_request

logger = init_logger("gateway.manager")


async def process_request(
    service: Union[str, None] = None,
    action: Union[str, None] = None,
    request: Union[Request, None] = None
):
    # Determine content type and parse accordingly
    request_data, content_type = await parse_request(request)

    # Construct the URL path
    path = f"{action}" if action else ""
    url = f"{settings.SERVICE_MAP.get(service)}/{path}"
    if 'None' in url:
        return {
            "message": "Service not found",
            "status_code": status.HTTP_404_NOT_FOUND
        }

    return await forward_request_and_process_response(url, request.method, content_type, request_data)


async def forward_request_and_process_response(
        url: str,
        method: str,
        content_type: str,
        request_data: Dict[str, Any]) -> Dict[str, Any]:
    try:

        if method == "POST":
            time = datetime.datetime.now()
            if content_type == 'json':
                response = await post(url, json=request_data, timeout=150000)
            elif content_type == 'multipart':
                files = {key: (file.filename, file.file, file.content_type) for key, file in request_data.items()
                         if isinstance(file, StarletteUploadFile)}
                data = {key: str(value) for key, value in request_data.items() if
                        not isinstance(value, StarletteUploadFile)}
                response = await post(url, data=data, files=files, timeout=150000)
            else:
                response = await post(url, data=request_data, timeout=150000)
            end_time = datetime.datetime.now()
            logger.info(f"Time taken: {end_time - time} with response: {response.get('status_code')}")
            return response
        else:
            return {
                "message": "Method not supported",
                "status_code": status.HTTP_405_METHOD_NOT_ALLOWED
            }
    except Exception as e:
        return {
            "message": str(e),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
