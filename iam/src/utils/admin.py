from auth_gateway_serverkit.logger import init_logger
from domains.users.db.mongo.user import find_by_username
from core.config import settings


logger = init_logger(__name__)


def is_admins(roles: list[str]) -> bool:
    """
    Check if the user has admin or systemAdmin roles
    :param roles:
    :return: bool
    """
    if not settings.has_system_admin_role_id() or not settings.has_admin_role_id():
        logger.error("Admin role IDs are not set. Denying access. Check lifespan initialization.")
        return False
    return bool({settings.SYSTEM_ADMIN_ROLE_ID, settings.ADMIN_ROLE_ID} & set(roles))


def is_system_admin(roles: list[str]) -> bool:
    """Check if user has the systemAdmin role specifically."""
    if not settings.has_system_admin_role_id():
        return False
    return settings.SYSTEM_ADMIN_ROLE_ID in roles


def check_org_scope(request_user: dict, target_org_id: str) -> bool:
    """
    Check if the requesting user has access to the target org.
    systemAdmin: unrestricted. admin: must be member of target org.
    """
    if is_system_admin(request_user.get("roles", [])):
        return True
    return target_org_id in request_user.get("organizations", [])


def check_user_org_overlap(request_user: dict, target_user_orgs: list) -> bool:
    """
    Check if the requesting user shares at least one org with target user.
    systemAdmin: unrestricted.
    """
    if is_system_admin(request_user.get("roles", [])):
        return True
    requester_orgs = set(request_user.get("organizations", []))
    return bool(requester_orgs & set(target_user_orgs))


async def fetch_system_admin_id() -> str:
    """
    Fetch the system admin user id
    :return: str
    """
    user = await find_by_username("sysadmin")
    if not user:
        raise Exception("System admin user not found")
    return str(user.id)


async def set_admins_role_ids() -> bool:
    """
    Set the system admin and admin role IDs in the settings.
    """
    try:
        from auth_gateway_serverkit.keycloak.role import get_all_roles
        roles = await get_all_roles()
        if not roles or roles.get("status") != "success":
            return False
        for role in roles["roles"]:
            if role["name"] == "systemAdmin":
                settings.set_system_admin_role_id(role["id"])
            elif role["name"] == "admin":
                settings.set_admin_role_id(role["id"])
        return True
    except Exception as e:
        logger.error(f"Failed to set admin role IDs: {str(e)}")
        return False
