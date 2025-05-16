from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse
from typing import Union
from config import settings
from manager import process_request, get_by_keycloak_uid, handle_login
from schemas import Login
from auth_gateway_serverkit.middleware.auth import auth
import uvicorn

app = FastAPI(title="gateway.app")


@app.get("/ping")
async def ping():
    return JSONResponse(content="pong!", status_code=status.HTTP_200_OK)


@app.post("/api/login")
async def login(request: Login):
    try:
        login_response = await handle_login(request)
        if login_response.status_code == status.HTTP_200_OK:
            # Extract the token from the response
            res = login_response.json()
            data = {
                "access_token": res.get("access_token"),
                "expires_in": res.get("expires_in"),
                "refresh_expires_in": res.get("refresh_expires_in"),
                "refresh_token": res.get("refresh_token"),
            }
            return JSONResponse(content=data, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content=login_response.json(), status_code=login_response.status_code)
    except Exception as e:
        return JSONResponse(
            content={"message": f"Internal Server Error: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.post("/api/{service}/{action}")
@app.put("/api/{service}/{action}")
@app.get("/api/{service}/{action}")
@app.delete("/api/{service}/{action}/{path:path}")
@app.get("/api/{service}/{action}/{path:path}")
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


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.reload
    )
