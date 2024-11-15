from typing import Any, Tuple, Optional
from fastapi import Request, status
from pydantic import ValidationError


async def parse_request(request):
    """Parse request based on content type."""
    content_type = request.headers.get('content-type', '').lower()

    if 'application/json' in content_type:
        return await parse_json_request(request)
    elif 'multipart/form-data' in content_type:
        return await parse_multipart_request(request)
    else:
        return await parse_form_request(request)


async def parse_json_request(request):
    """Parse JSON request."""
    request_data = await request.json()
    return request_data, 'json'


async def parse_multipart_request(request):
    """Parse multipart form-data request."""
    form = await request.form()
    request_data = {key: value for key, value in form.multi_items()}
    return request_data, 'multipart'


async def parse_form_request(request):
    """Parse regular form-urlencoded request."""
    form = await request.form()
    request_data = {key: value for key, value in form.multi_items()}
    return request_data, 'form'
