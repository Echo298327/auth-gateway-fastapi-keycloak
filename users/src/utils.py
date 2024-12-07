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

