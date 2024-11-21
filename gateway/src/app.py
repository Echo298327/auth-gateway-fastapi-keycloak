from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse
from middleware.auth import auth
from typing import Union
from config import settings
from manager import process_request, get_by_keycloak_uid
import uvicorn


app = FastAPI(title="Gateway App")


@app.post("/api/{service}/{action}")
@auth(get_user_by_uid=get_by_keycloak_uid)
async def handle_request(
    request: Request,
    service: Union[str, None] = None,
    action: Union[str, None] = None,
):
    try:
        # Process the request
        response = await process_request(service, action, request)

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


@app.get("/ping")
async def ping():
    return {"message": "pong!", "status_code": status.HTTP_200_OK}


if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=True)