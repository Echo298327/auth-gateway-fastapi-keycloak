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
        logger.warning(
            "System admin or admin role IDs are not set in settings. Attempting to set them."
        )
        set_admins_role_ids()
    return bool({settings.SYSTEM_ADMIN_ROLE_ID, settings.ADMIN_ROLE_ID} & set(roles))


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
        from auth_gateway_serverkit.keycloak.roles_api import get_all_roles
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
