from mongo_models import User
from auth_gateway_serverkit.string import is_valid_user_name, is_valid_name


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
    return bool({"admin", "systemAdmin"} & set(roles))


def fetch_system_admin_id() -> str:
    """
    Fetch the system admin user id
    :return: str
    """
    return User.objects(roles__in=["systemAdmin"], user_name="sysadmin").first().id
