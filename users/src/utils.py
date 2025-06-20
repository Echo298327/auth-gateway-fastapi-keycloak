from auth_gateway_serverkit.string import is_valid_user_name, is_valid_name
from auth_gateway_serverkit.logger import init_logger

try:
    from mongo_models import User
    from config import settings
except ImportError:
    from .mongo_models import User
    from .config import settings


logger = init_logger("users.utils")


def is_valid_roles(provided_role_names: list[str], keycloak_roles: list[dict]) -> bool:
    """
    Validate that all provided role names exist in the roles returned from Keycloak.

    Args:
        provided_role_names (list[str]): Role names received in the request.
        keycloak_roles (list[dict]): Roles fetched from Keycloak, each expected to have a 'name' field.

    Returns:
        bool: True if all provided roles are valid and role list is well-formed, False otherwise.
    """
    if not isinstance(keycloak_roles, list):
        logger.error("keycloak_roles is not a list.")
        return False

    if not all(isinstance(role, dict) and 'name' in role for role in keycloak_roles):
        logger.error("keycloak_roles contains invalid entries.")
        return False

    valid_role_names = {role['name'] for role in keycloak_roles}
    invalid = [name for name in provided_role_names if name not in valid_role_names]

    if invalid:
        logger.error(f"Invalid roles requested: {invalid}")
        return False

    return True


def is_valid_names(user_name: str = None, first_name: str = None, last_name: str = None) -> tuple[bool, list[str]]:
    errors = []

    if user_name and not is_valid_user_name(user_name):
        errors.append("Invalid user name")
    if first_name and not is_valid_name(first_name):
        errors.append("Invalid first name")
    if last_name and not is_valid_name(last_name):
        errors.append("Invalid last name")

    if errors:
        return False, errors

    return True, []


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


def fetch_system_admin_id() -> str:
    """
    Fetch the system admin user id
    :return: str
    """
    return User.objects(user_name="sysadmin").first().id


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
