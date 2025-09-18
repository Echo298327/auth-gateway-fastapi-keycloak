from auth_gateway_serverkit.logger import init_logger

logger = init_logger(__name__)


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