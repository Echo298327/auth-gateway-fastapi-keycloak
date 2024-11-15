import httpx
import json
from fastapi import Request
from typing import Optional
from logger import init_logger
from urllib.parse import urlparse, urlunparse


logger = init_logger("utils.requests")


async def post(
    url: str,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    files: Optional[dict] = None,
    timeout=20,
    connect=5
) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if json is not None:
                response = await client.post(url, json=json)
            elif files is not None or data is not None:
                response = await client.post(url, data=data, files=files)
            else:
                response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text} - URL: {url}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e} - URL: {url}")
        raise


async def get(url: str, params: dict = None, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e}")
        raise


async def delete(url: str, json: dict = None, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.delete(url, json=json)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e}")
        raise


async def put(url: str, json: Optional[dict] = None, data: Optional[dict] = None, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)

        async with httpx.AsyncClient(timeout=timeout) as client:
            if json is not None:
                response = await client.put(url, json=json)
            else:
                response = await client.put(url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text} - URL: {url}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e} - URL: {url}")
        raise


async def pass_auth_request(request: Request, product: str, sense_domain: str, timeout=20, connect=5):
    new_url = ""
    try:
        original_url = request.url
        parsed_url = urlparse(str(original_url))

        new_path = parsed_url.path.replace('/api', '/auth', 1)

        if not sense_domain.startswith(('http://', 'https://')):
            sense_domain = f"{parsed_url.scheme}://{sense_domain}"

        parsed_domain = urlparse(sense_domain)

        new_url = urlunparse((
            parsed_domain.scheme,
            parsed_domain.netloc,
            new_path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment
        ))

        try:
            body = await request.json()
        except json.JSONDecodeError:
            body = {}

        auth_body = {**body, 'product': product}

        headers = {k: v for k, v in request.headers.items()
                   if k.lower() not in ['host', 'content-length', 'content-type']}
        headers['content-type'] = 'application/json'

        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                new_url,
                json=auth_body,
                headers=headers
            )

        return response
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text} - URL: {new_url}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e} - URL: {new_url}")
        raise
