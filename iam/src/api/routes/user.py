from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from typing import Tuple, List, Any, Dict
from core.config import settings
from domains.users.schemas import CreateUser, UpdateUser, DeleteUser, GetUser, GetUserByKeycloakUid
from auth_gateway_serverkit.request_handler import parse_request_body_to_model, response, get_request_user
from auth_gateway_serverkit.logger import init_logger
from domains.users.services import manager

router = APIRouter()

logger = init_logger(__name__)


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


@router.get("/ping")
async def ping():
    return JSONResponse(content="pong!", status_code=status.HTTP_200_OK)


@router.post("/create")
async def create_user(data_errors: Tuple[CreateUser, List[str]] = Depends(parse_request_body_to_model(CreateUser))):
    return await handle_request(data_errors, manager.create_user)


@router.put("/update")
async def update_user(
        data_errors: Tuple[UpdateUser, List[str]] = Depends(parse_request_body_to_model(UpdateUser)),
        user: Dict[str, Any] = Depends(get_request_user)
):
    return await handle_request(data_errors, manager.update_user, user)


@router.delete("/delete/{user_id}")
async def delete_user(user_id: str):
    return await handle_request((DeleteUser(user_id=user_id), []), manager.delete_user)


@router.get("/get")
@router.get("/get/{user_id}")
async def get_user(user_id: str = None, user: Dict[str, Any] = Depends(get_request_user)):
    data_errors = (GetUser(user_id=user_id), [])
    return await handle_request(data_errors, manager.get_user, user)


@router.get("/get_by_keycloak_uid/{keycloak_uid}")
async def get_user_by_keycloak_uid(keycloak_uid: str):
    data_errors = (GetUserByKeycloakUid(keycloak_uid=keycloak_uid), [])
    return await handle_request(data_errors, manager.get_user_by_keycloak_uid)


@router.get("/get_sys_id")
async def get_system_admin_id():
    return await settings.get_system_admin_id()


@router.get("/roles")
async def get_roles(user: Dict[str, Any] = Depends(get_request_user)):
    try:
        roles = await manager.get_roles(user)
        return response(res=roles)
    except Exception as e:
        return response(error=str(e))

