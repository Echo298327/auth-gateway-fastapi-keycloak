from fastapi import APIRouter, Request, status
from starlette.responses import JSONResponse
from typing import Union
from services.manager import process_request, get_by_keycloak_uid, handle_login, handle_refresh, handle_logout
from schemas.gateway import Login, Refresh
from auth_gateway_serverkit.middleware.auth import auth
from auth_gateway_serverkit.middleware.auth import get_user_info


router = APIRouter()


@router.get("/ping")
async def ping():
    return JSONResponse(content="pong!", status_code=status.HTTP_200_OK)


@router.post("/api/login")
async def login(request: Login):
    try:
        login_response = await handle_login(request)
        if login_response.status_code == status.HTTP_200_OK:
            # Extract the token from the response
            res = login_response.json()
            user_payload = await get_user_info(res.get("access_token"))
            user = await get_by_keycloak_uid(user_payload.id)
            if user is None:
                return JSONResponse(
                    content={"message": "User not found"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            data = {
                "access_token": res.get("access_token"),
                "expires_in": res.get("expires_in"),
                "refresh_expires_in": res.get("refresh_expires_in"),
                "refresh_token": res.get("refresh_token"),
                "user": user,
            }
            return JSONResponse(content=data, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content=login_response.json(), status_code=login_response.status_code)
    except Exception as e:
        return JSONResponse(
            content={"message": f"Internal Server Error: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/api/refresh")
async def refresh(request: Refresh):
    try:
        refresh_response = await handle_refresh(request.refresh_token)
        if refresh_response is None:
            return JSONResponse(
                content={"message": "Failed to refresh token"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if refresh_response.status_code == status.HTTP_200_OK:
            res = refresh_response.json()
            user_payload = await get_user_info(res.get("access_token"))
            user = await get_by_keycloak_uid(user_payload.id)
            if user is None:
                return JSONResponse(
                    content={"message": "User not found"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            data = {
                "access_token": res.get("access_token"),
                "expires_in": res.get("expires_in"),
                "refresh_expires_in": res.get("refresh_expires_in"),
                "refresh_token": res.get("refresh_token"),
                "user": user,
            }
            return JSONResponse(content=data, status_code=status.HTTP_200_OK)
        return JSONResponse(
            content=refresh_response.json(),
            status_code=refresh_response.status_code
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Internal Server Error: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/api/logout")
async def logout(request: Refresh):
    try:
        logout_response = await handle_logout(request.refresh_token)
        if logout_response is None:
            return JSONResponse(
                content={"message": "Failed to revoke token"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if logout_response.status_code in (200, 204):
            return JSONResponse(
                content={"message": "Logged out successfully"},
                status_code=status.HTTP_200_OK
            )
        return JSONResponse(
            content=logout_response.json() if logout_response.content else {"message": "Logout failed"},
            status_code=logout_response.status_code
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Internal Server Error: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.api_route("/api/{service}/{action}", methods=["GET", "POST", "PUT", "DELETE"])
@router.api_route("/api/{service}/{action}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@auth(get_user_by_uid=get_by_keycloak_uid)
async def handle_request(
    request: Request,
    service: Union[str, None] = None,
    action: Union[str, None] = None,
    path: Union[str, None] = None
):
    try:
        # Process the request
        response = await process_request(service, action, request, path)

        # Extract the status code from the response, defaulting to 400 if not found
        status_code = response.pop("status_code", status.HTTP_400_BAD_REQUEST)

        # Extract the data from the response if it exists
        data = response.get("data", response)

        # Return the JSON response with the appropriate status code
        return JSONResponse(content=data, status_code=status_code)
    except Exception as e:

        return JSONResponse(
            content={"message": f"Internal Server Error: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )