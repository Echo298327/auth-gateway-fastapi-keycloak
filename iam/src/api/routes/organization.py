from fastapi import APIRouter, Depends
from typing import Tuple, List, Any, Dict
from domains.organizations.schemas import (
    CreateOrganization, UpdateOrganization, DeleteOrganization,
    GetOrganization, AddUserToOrg, RemoveUserFromOrg,
)
from auth_gateway_serverkit.request_handler import parse_request_body_to_model, response, get_request_user
from auth_gateway_serverkit.logger import init_logger
from domains.organizations.services import manager

router = APIRouter()

logger = init_logger(__name__)


async def handle_request(
    data_errors: Tuple[Any, List[str]],
    action: callable,
    user: Dict[str, Any] = None,
):
    try:
        data, errors = data_errors
        if errors:
            return response(validation_errors=errors)
        if user is not None:
            res = await action(data, user)
        else:
            res = await action(data)
        return response(res=res)
    except Exception as e:
        return response(error=str(e))


@router.post("/create")
async def create_organization(
    data_errors: Tuple[CreateOrganization, List[str]] = Depends(parse_request_body_to_model(CreateOrganization)),
):
    return await handle_request(data_errors, manager.create_org)


@router.put("/update")
async def update_organization(
    data_errors: Tuple[UpdateOrganization, List[str]] = Depends(parse_request_body_to_model(UpdateOrganization)),
    user: Dict[str, Any] = Depends(get_request_user),
):
    return await handle_request(data_errors, manager.update_org, user)


@router.delete("/delete/{org_id}")
async def delete_organization(org_id: str):
    return await handle_request((DeleteOrganization(org_id=org_id), []), manager.delete_org)


@router.get("/get")
@router.get("/get/{org_id}")
async def get_organization(org_id: str = None, user: Dict[str, Any] = Depends(get_request_user)):
    data_errors = (GetOrganization(org_id=org_id), [])
    return await handle_request(data_errors, manager.get_org, user)


@router.post("/add_user")
async def add_user_to_organization(
    data_errors: Tuple[AddUserToOrg, List[str]] = Depends(parse_request_body_to_model(AddUserToOrg)),
    user: Dict[str, Any] = Depends(get_request_user),
):
    return await handle_request(data_errors, manager.add_user_to_org, user)


@router.post("/remove_user")
async def remove_user_from_organization(
    data_errors: Tuple[RemoveUserFromOrg, List[str]] = Depends(parse_request_body_to_model(RemoveUserFromOrg)),
    user: Dict[str, Any] = Depends(get_request_user),
):
    return await handle_request(data_errors, manager.remove_user_from_org, user)


@router.get("/members/{org_id}")
async def get_organization_members(org_id: str, user: Dict[str, Any] = Depends(get_request_user)):
    data_errors = (GetOrganization(org_id=org_id), [])
    return await handle_request(data_errors, manager.get_members, user)
