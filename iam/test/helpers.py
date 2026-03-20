"""Shared test constants and helper functions."""

SYSTEM_ADMIN_ROLE_ID = "role-sysadmin-111"
ADMIN_ROLE_ID = "role-admin-222"
ORG_A_ID = "aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ORG_B_ID = "bbbb2222-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
SYSTEM_ADMIN_USER_ID = "sys-admin-id-000"


def make_user(user_id, roles, organizations):
    """Build a request_user dict matching the gateway payload structure."""
    return {"id": user_id, "roles": roles, "organizations": organizations}


def sys_admin_user():
    return make_user(SYSTEM_ADMIN_USER_ID, [SYSTEM_ADMIN_ROLE_ID], [])


def admin_user_a():
    return make_user("admin-a-id", [ADMIN_ROLE_ID], [ORG_A_ID])


def admin_user_b():
    return make_user("admin-b-id", [ADMIN_ROLE_ID], [ORG_B_ID])


def admin_user_ab():
    return make_user("admin-ab-id", [ADMIN_ROLE_ID], [ORG_A_ID, ORG_B_ID])


def regular_user_a():
    return make_user("user-a-id", ["role-user-333"], [ORG_A_ID])


class UpdateUserData:
    """Payload for UserManager.update_user tests; provides model_dump like Pydantic models."""

    def __init__(
        self,
        *,
        user_id=None,
        user_name=None,
        first_name=None,
        last_name=None,
        email=None,
        roles=None,
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.roles = roles

    def model_dump(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "roles": self.roles,
        }
