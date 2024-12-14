import uvicorn
from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from typing import Tuple, List, Any, Dict
from config import settings
from schemas import CreateUser, UpdateUser, DeleteUser, GetUser, GetUserByKeycloakUid
from auth_gateway_serverkit.request_handler import parse_request_body_to_model, response, get_request_user
from auth_gateway_serverkit.keycloak.initializer import initialize_keycloak_server
from manager import manager

app = FastAPI(title="user.app")


@app.on_event("startup")
async def startup_event():
    settings.connect_db()
    is_initialized = await initialize_keycloak_server()
    if not is_initialized:
        raise Exception("Failed to initialize Keycloak server")
    is_system_admin_created = await manager.create_system_admin()
    if not is_system_admin_created:
        raise Exception("Failed to create system admin")


async def handle_request(
    data_errors: Tuple[Any, List[str]],
    action: callable,
    user: Dict[str, Any] = None
):
    try:
        data, errors = data_errors
        if errors:
            return response(validation_errors=errors)
        if user:
            res = await action(data, user)
        else:
            res = await action(data)
        return response(res=res)
    except Exception as e:
        return response(error=str(e))


@app.get("/ping")
async def ping():
    return JSONResponse(content="pong!", status_code=status.HTTP_200_OK)


@app.post("/create")
async def create_user(data_errors: Tuple[CreateUser, List[str]] = Depends(parse_request_body_to_model(CreateUser))):
    return await handle_request(data_errors, manager.create_user)


@app.put("/update")
async def update_user(
        data_errors: Tuple[UpdateUser, List[str]] = Depends(parse_request_body_to_model(UpdateUser)),
        user: Dict[str, Any] = Depends(get_request_user)
):
    return await handle_request(data_errors, manager.update_user, user)


@app.delete("/delete/{user_id}")
async def delete_user(user_id: str):
    return await handle_request((DeleteUser(user_id=user_id), []), manager.delete_user)


@app.get("/get/{user_id}")
async def get_user(user_id: str, user: Dict[str, Any] = Depends(get_request_user)):
    data_errors = (GetUser(user_id=user_id), [])
    return await handle_request(data_errors, manager.get_user, user)


@app.get("/get_by_keycloak_uid/{keycloak_uid}")
async def get_user_by_keycloak_uid(keycloak_uid: str):
    data_errors = (GetUserByKeycloakUid(keycloak_uid=keycloak_uid), [])
    return await handle_request(data_errors, manager.get_user_by_keycloak_uid)


if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=True)
