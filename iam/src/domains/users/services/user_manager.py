from auth_gateway_serverkit.logger import init_logger
from auth_gateway_serverkit.password import generate_password
from auth_gateway_serverkit.keycloak.user_api import (
    add_user_to_keycloak, update_user_in_keycloak, delete_user_from_keycloak
)
from auth_gateway_serverkit.keycloak.roles_api import get_all_roles, get_role_by_name

from core.config import settings
from domains.users.db.mongo.user import (
    find_by_username, find_by_user_id, find_by_keycloak_uid, 
    create_user, update_user, delete_user, check_username_exists,
    check_email_exists, user_exists
)
from domains.users.schemas import AllowedRoles
from utils.roles import is_valid_roles
from utils.validation import is_valid_names
from utils.admin import is_admins
from utils.exception_handler import exception_handler



class UserManager:
    def __init__(self):
        self.logger = init_logger(__name__)

    @exception_handler("error creating system admin")
    async def create_system_admin(self) -> bool:
        # Check if system admin already exists
        user = await find_by_username(settings.SYSTEM_ADMIN_USER_NAME)
        if user:
            return True

        response = await add_user_to_keycloak(
            settings.SYSTEM_ADMIN_USER_NAME,
            settings.SYSTEM_ADMIN_FIRST_NAME,
            settings.SYSTEM_ADMIN_LAST_NAME,
            settings.SYSTEM_ADMIN_EMAIL,
            settings.SYSTEM_ADMIN_PASSWORD,
            ["systemAdmin"],
        )

        if response.get('status') != 'success':
            raise Exception(f"Failed to create system admin in Keycloak: {response.get('message')}")

        keycloak_uid = response.get('keycloakUserId')
        if not keycloak_uid:
            raise Exception("Failed to get keycloak user id")

        # get the role IDs from Keycloak
        realm_role = await get_role_by_name("systemAdmin")
        if not realm_role or realm_role.get('status') != 'success':
            raise Exception("Failed to get systemAdmin role from Keycloak")

        role = realm_role.get('role', {})
        role_ids = [role['id']] if role.get('name') == "systemAdmin" else []

        user = await create_user(
            user_name=settings.SYSTEM_ADMIN_USER_NAME,
            first_name=settings.SYSTEM_ADMIN_FIRST_NAME,
            last_name=settings.SYSTEM_ADMIN_LAST_NAME,
            roles=role_ids,
            email=settings.SYSTEM_ADMIN_EMAIL,
            keycloak_uid=keycloak_uid,
        )

        # Verify the user was created
        if not await user_exists(user.id):
            raise Exception("Failed to verify the saved system admin")

        self.logger.info(f"System admin created: {user.id}")
        return True

    @exception_handler("error creating user")
    async def create_user(self, data) -> dict:
        """
        Create a new user in the database and in Keycloak.

        Args:
            data: Data object containing user information such as user_name,
                  first_name, last_name, email, and roles.

        Returns:
            dict: A dictionary containing the result of the operation.
        """
        user_name = data.user_name.lower()
        first_name = data.first_name
        last_name = data.last_name
        email = data.email
        roles = data.roles

        valid_names, errors = is_valid_names(user_name, first_name, last_name)
        if not valid_names:
            raise Exception(", ".join(errors))

        # Check if username or email already exists
        if await check_username_exists(user_name):
            raise Exception(f"Username '{user_name}' already exists")
        
        if await check_email_exists(email):
            raise Exception(f"Email '{email}' already exists")

        role_names = [role.value if isinstance(role, AllowedRoles) else role for role in roles]
        realm_roles = await get_all_roles()

        if not is_valid_roles(role_names, realm_roles.get('roles', [])):
            raise Exception("Invalid roles provided")
        roles = [role.value if isinstance(role, AllowedRoles) else role for role in roles]
        role_ids = [role['id'] for role in realm_roles.get('roles', []) if role['name'] in role_names]

        password = generate_password()
        response = await add_user_to_keycloak(user_name, first_name, last_name, email, password, roles)

        if response.get('status') != 'success':
            raise Exception(f"Error creating user in Keycloak: {response.get('message')}")

        keycloak_uid = response.get('keycloakUserId')
        if not keycloak_uid:
            raise Exception("Failed to get Keycloak user ID")

        # If Keycloak creation succeeds but database fails, we need to clean up Keycloak
        try:
            user = await create_user(
                user_name=user_name,
                first_name=first_name,
                last_name=last_name,
                roles=role_ids,
                email=email,
                keycloak_uid=keycloak_uid,
            )
        except Exception as e:
            # Rollback Keycloak user creation if database creation fails
            rollback_response = await delete_user_from_keycloak(keycloak_uid)
            if rollback_response.get('status') != 'success':
                self.logger.error(f"Failed to rollback Keycloak user {keycloak_uid}: {rollback_response.get('message')}")
            raise e

        self.logger.info(f"User created: {user.id}")
        return {"status": "success", "user_id": str(user.id), "message": "User created successfully"}

    @exception_handler("error updating user")
    async def update_user(self, data, request_user=None) -> dict:
        """
        Update an existing user in the database and in Keycloak.

        Args:
            data: An object containing the user_id and the fields to update.
            request_user (optional): The user object (dict) making the request.
                                     This object is provided by the gateway and
                                     helps determine authorization. It is not
                                     used by STS requests directly.

        Returns:
            dict: A dictionary containing the status and message of the operation.
        """
        is_keycloak_update_needed = False
        
        if data.user_id == await settings.get_system_admin_id():
            raise Exception("System admin user cannot be updated")

        roles = data.roles if data.roles else []
        if not data.user_id:
            user_id = request_user.get("id")
        else:
            if not is_admins(request_user.get("roles")) and data.user_id != request_user.get("id"):
                raise Exception("Unauthorized to update user")
            user_id = data.user_id
        user_name = data.user_name.lower() if data.user_name else None

        if roles:
            role_names = [role.value if isinstance(role, AllowedRoles) else role for role in roles]
            realm_roles = await get_all_roles()
            if not is_valid_roles(role_names, realm_roles.get('roles', [])):
                raise Exception("Invalid roles provided")

            roles = [role.value if isinstance(role, AllowedRoles) else role for role in roles]
            role_ids = [role['id'] for role in realm_roles.get('roles', []) if role['name'] in role_names]

        user = await find_by_user_id(user_id)
        if not user:
            raise Exception(f"User not found with ID: {user_id}")

        if user_name and user_name != user.user_name:
            if await check_username_exists(user_name, exclude_user_id=user_id):
                raise Exception(f"Username '{user_name}' already exists")

        valid_names, errors = is_valid_names(user_name, data.first_name, data.last_name)
        if not valid_names:
            raise Exception(", ".join(errors))

        # Check if the requester has the necessary permissions
        user_roles = request_user.get("roles") if request_user else None
        if roles and not is_admins(user_roles):
            raise Exception("Unauthorized to update roles")

        # Prepare update fields
        update_fields = {}
        if user_name is not None:
            update_fields["user_name"] = user_name
        if data.first_name is not None:
            update_fields["first_name"] = data.first_name
        if data.last_name is not None:
            update_fields["last_name"] = data.last_name
        if data.email is not None:
            update_fields["email"] = data.email
        if roles:
            update_fields["roles"] = role_ids

        # Update user in database
        updated_user = await update_user(user, **update_fields)

        # Update in Keycloak if needed
        if any(field in data.dict() for field in ["user_name", "first_name", "last_name", "email", "roles"]):
            is_keycloak_update_needed = True
            response = await update_user_in_keycloak(
                updated_user.keycloak_uid,
                updated_user.user_name,
                updated_user.first_name,
                updated_user.last_name,
                updated_user.email,
                roles if roles else None,
            )

            if response.get("status") != "success":
                raise Exception(f"Keycloak update error: {response.get('message', 'Unknown error')}")

        return {
            "status": "success",
            "message": f"User updated successfully. {'A new login token will be needed.' if is_keycloak_update_needed else ''}"
        }

    @exception_handler("error deleting user")
    async def delete_user(self, data) -> dict:
        """
        Delete a user from the database and from Keycloak.

        Args:
            data: An object containing the user_id of the user to delete.

        Returns:
            dict: A dictionary containing the status and message of the operation.
        """
        user_id = data.user_id
        user = await find_by_user_id(user_id)

        if not user:
            raise Exception(f"User not found with ID: {user_id}")

        keycloak_response = await delete_user_from_keycloak(user.keycloak_uid)
        if keycloak_response.get('status') != 'success':
            raise Exception(f"Error deleting user from Keycloak: {keycloak_response.get('message', 'Unknown error')}")

        success = await delete_user(user_id)
        if not success:
            raise Exception(f"Failed to delete user from database: {user_id}")
        
        self.logger.info(f"User deleted: {user_id}")
        return {"status": "success", "message": "User deleted successfully"}

    @exception_handler("error getting user")
    async def get_user(self, data, request_user=None) -> dict:
        """
        Retrieve a user's information from the database.

        Args:
            data: An object containing the user_id of the user to retrieve.
            request_user (optional): The user object (dict) making the request.
                                     This object is provided by the gateway and
                                     is used to ensure that the requester has
                                     the necessary permissions. It is not used
                                     by STS requests directly.

        Returns:
            dict: A dictionary containing the status and user data if found.
        """
        # Check if the requester has the necessary permissions
        if request_user and data.user_id:
            if request_user.get("id") != data.user_id and not is_admins(request_user.get("roles", [])):
                raise Exception("Unauthorized access to user data")

        if request_user and not data.user_id:
            user_id = request_user.get("id")
        else:
            user_id = data.user_id
        
        user = await find_by_user_id(user_id)
        if not user:
            raise Exception(f"User not found with ID: {user_id}")

        user_data = {
            "id": str(user.id),
            "user_name": user.user_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.roles,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        return {"status": "success", "data": user_data}

    @exception_handler("error getting user by keycloak uid")
    async def get_user_by_keycloak_uid(self, data) -> dict:
        """
        Retrieve a user's information from the database using their Keycloak UID.

        Args:
            data: An object containing the keycloak_uid of the user.

        Returns:
            dict: A dictionary containing the status and user data if found.
        """
        keycloak_uid = data.keycloak_uid
        user = await find_by_keycloak_uid(keycloak_uid)
        if not user:
            raise Exception(f"User not found with Keycloak UID: {keycloak_uid}")

        user_dict = {
            "id": str(user.id),
            "user_name": user.user_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.roles,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
        # Remove keycloak_uid for security reasons - it's not included in the dict
        return {"status": "success", "data": user_dict}

    @exception_handler("error getting roles")
    async def get_roles(self, request_user=None) -> dict:
        """
        Retrieve all custom (non-default) roles from Keycloak.
        The systemAdmin role is only available to the system admin user.

        Args:
            request_user (optional): The user object making the request.

        Returns:
            dict: A dictionary containing the status and list of custom roles.
        """
        realm_roles = await get_all_roles()
        if realm_roles.get('status') != 'success':
            raise Exception("Failed to retrieve roles from Keycloak")

        roles = realm_roles.get('roles', [])

        def is_custom_role(role: dict) -> bool:
            return not (
                role["name"].startswith("default-roles-") or
                role["name"] in {"offline_access", "uma_authorization"} or
                role.get("description", "").startswith("${role_")
            )

        custom_roles = [role for role in roles if is_custom_role(role)]
        
        # Filter out systemAdmin role unless the requester is the system admin
        if request_user:
            user_id = request_user.get("id")
            system_admin_id = await settings.get_system_admin_id()
            
            if user_id != system_admin_id:
                custom_roles = [role for role in custom_roles if role["name"] != "systemAdmin"]
        else:
            # If no request_user, assume it's not the system admin and filter out systemAdmin
            custom_roles = [role for role in custom_roles if role["name"] != "systemAdmin"]

        return {"status": "success", "data": custom_roles}


manager = UserManager()
