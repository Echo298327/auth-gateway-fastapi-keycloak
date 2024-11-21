import manager
import uvicorn
from fastapi import FastAPI, Depends
from config import settings
from schemas import CreateUser, UpdateUser, DeleteUser, GetUser, GetUserByKeycloakUid
from typing import Tuple, List, Any
from request_handler import parse_json_request, response
from keycloak_init import initialize_keycloak_server

app = FastAPI(title="User App")


@app.on_event("startup")
async def startup_event():
    settings.connect_db()
    is_initialized = await initialize_keycloak_server()
    if not is_initialized:
        raise Exception("Failed to initialize Keycloak server")


async def handle_request(
    data_errors: Tuple[Any, List[str]],
    action: callable
):
    try:
        data, errors = data_errors
        if errors:
            return response(validation_errors=errors)
        res = await action(data)
        return response(res=res)
    except Exception as e:
        return response(error=str(e))


@app.post("/create")
async def create_user(data_errors: Tuple[CreateUser, List[str]] = Depends(parse_json_request(CreateUser))):
    return await handle_request(data_errors, manager.create_user)


@app.post("/update")
async def update_user(data_errors: Tuple[UpdateUser, List[str]] = Depends(parse_json_request(UpdateUser))):
    return await handle_request(data_errors, manager.update_user)


@app.post("/delete")
async def delete_user(data_errors: Tuple[DeleteUser, List[str]] = Depends(parse_json_request(DeleteUser))):
    return await handle_request(data_errors, manager.delete_user)


@app.post("/get")
async def get_user(data_errors: Tuple[GetUser, List[str]] = Depends(parse_json_request(GetUser))):
    return await handle_request(data_errors, manager.get_user)


@app.post("/get_by_keycloak_uid")
async def get_user_by_keycloak_uid(data_errors: Tuple[GetUserByKeycloakUid, List[str]] = Depends(parse_json_request(GetUserByKeycloakUid))):
    return await handle_request(data_errors, manager.get_user_by_keycloak_uid)


if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=True)
