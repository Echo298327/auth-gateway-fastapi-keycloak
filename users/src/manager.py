import time
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError
from mongoengine import get_db
from auth_gateway_serverkit.logger import init_logger
from auth_gateway_serverkit.password import generate_password
from auth_gateway_serverkit.keycloak.user_api import (
    add_user_to_keycloak, update_user_in_keycloak, delete_user_from_keycloak
)
# from auth_gateway_serverkit.email import send_password_email

try:
    from config import settings
    from mongo_models import User
    from schemas import AllowedRoles
    from utils import is_valid_names,is_admins
except ImportError:
    from .config import settings
    from .mongo_models import User
    from .schemas import AllowedRoles
    from .utils import is_valid_names,is_admins


def exception_handler(func):
    """A decorator to handle exceptions and return standardized responses."""
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except ValidationError as ve:
            self.logger.error(f"Validation error: {ve}")
            return {"status": "failed", "message": str(ve)}
        except NotUniqueError:
            self.logger.error("Duplicate key error")
            return {"status": "failed", "message": "User already exists"}
        except DoesNotExist:
            self.logger.error("User not found")
            return {"status": "failed", "message": "User not found"}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"status": "failed", "message": "Internal Server Error"}
    return wrapper


class UserManager:
    def __init__(self):
        self.logger = init_logger("user.manager")

    @exception_handler
    async def create_system_admin(self) -> bool:
        # No session needed because it's a one-time creation
        user = User.objects(user_name=settings.SYSTEM_ADMIN_USER_NAME).first()
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
            self.logger.error(f"Failed to create system admin in Keycloak: {response.get('message')}")
            return False

        keycloak_uid = response.get('keycloakUserId')
        if not keycloak_uid:
            self.logger.error("Failed to get keycloak user id")
            return False

        user = User(
            user_name=settings.SYSTEM_ADMIN_USER_NAME,
            first_name=settings.SYSTEM_ADMIN_FIRST_NAME,
            last_name=settings.SYSTEM_ADMIN_LAST_NAME,
            roles=["systemAdmin"],
            email=settings.SYSTEM_ADMIN_EMAIL,
            keycloak_uid=keycloak_uid,
            creation_date=time.strftime("%d-%m-%Y"),
        )
        user.save()

        if not User.objects(id=user.id).first():
            self.logger.error("Failed to verify the saved system admin.")
            return False

        self.logger.info(f"System admin created: {user.id}")
        return True

    @exception_handler
    async def create_user(self, data) -> dict:
        """
        Create a new user in the database and in Keycloak.

        Args:
            data: Data object containing user information such as user_name,
                  first_name, last_name, email, and roles.

        Returns:
            dict: A dictionary containing the result of the operation.
        """
        db = get_db()
        session = db.client.start_session()
        session.start_transaction()
        keycloak_uid = None
        try:
            user_name = data.user_name.lower()
            first_name = data.first_name
            last_name = data.last_name
            email = data.email
            roles = data.roles

            valid_names, errors = is_valid_names(user_name, first_name, last_name)
            if not valid_names:
                session.abort_transaction()
                session.end_session()
                return {"status": "failed", "message": ", ".join(errors)}

            roles = [role.value if isinstance(role, AllowedRoles) else role for role in roles]

            password = generate_password()
            response = await add_user_to_keycloak(user_name, first_name, last_name, email, password, roles)

            if response.get('status') != 'success':
                # Known keycloak creation failure
                session.abort_transaction()
                session.end_session()
                self.logger.error(f"Error creating user in Keycloak: {response.get('message')}")
                return {"status": "failed", "message": "Error creating user in Keycloak"}

            keycloak_uid = response.get('keycloakUserId')
            if not keycloak_uid:
                session.abort_transaction()
                session.end_session()
                self.logger.error("Failed to get Keycloak user ID")
                return {"status": "failed", "message": "Failed to get Keycloak user ID"}

            user = User(
                user_name=user_name,
                first_name=first_name,
                last_name=last_name,
                roles=roles,
                email=email,
                keycloak_uid=keycloak_uid,
                creation_date=time.strftime("%d-%m-%Y"),
            )
            user.save(force_insert=True, session=session)

            session.commit_transaction()
            self.logger.info(f"User created: {user.id}")
            return {"status": "success", "user_id": str(user.id), "message": "User created successfully"}

        except Exception:
            # Unexpected error case: let the decorator handle returning "Internal Server Error"
            session.abort_transaction()
            if keycloak_uid:
                # Attempt to roll back the Keycloak user creation
                rollback_response = await delete_user_from_keycloak(keycloak_uid)
                if rollback_response.get('status') != 'success':
                    self.logger.error(
                        f"Failed to rollback Keycloak user {keycloak_uid}: {rollback_response.get('message')}"
                    )
            raise
        finally:
            session.end_session()

    @exception_handler
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
        db = get_db()
        session = db.client.start_session()
        session.start_transaction()
        is_keycloak_update_needed = False
        try:
            if not data.user_id:
                user_id = request_user.get("id")
            else:
                if not is_admins(request_user.get("roles")) and data.user_id != request_user.get("id"):
                    session.abort_transaction()
                    session.end_session()
                    return {"status": "failed", "message": "Unauthorized to update user"}
                user_id = data.user_id
            user_name = data.user_name.lower() if data.user_name else None
            roles = \
                [role.value if isinstance(role, AllowedRoles) else role for role in data.roles] if data.roles else None

            user = User.objects(id=user_id).first()
            if not user:
                session.abort_transaction()
                session.end_session()
                return {"status": "failed", "message": "User not found"}

            if user_name and user_name != user.user_name:
                if User.objects(user_name=user_name, id__ne=user_id).first():
                    session.abort_transaction()
                    session.end_session()
                    return {"status": "failed", "message": "User name already exists"}

            valid_names, errors = is_valid_names(user_name, data.first_name, data.last_name)
            if not valid_names:
                session.abort_transaction()
                session.end_session()
                return {"status": "failed", "message": ", ".join(errors)}

            # Check if the requester has the necessary permissions
            user_roles = request_user.get("roles") if request_user else None
            if roles and not is_admins(user_roles):
                session.abort_transaction()
                session.end_session()
                return {"status": "failed", "message": "Unauthorized to update roles"}

            update_fields = {
                "user_name": user_name,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "email": data.email,
                "roles": roles
            }
            for field, value in update_fields.items():
                if value is not None:
                    setattr(user, field, value)

            user.save(session=session)

            # Update in Keycloak if needed
            if any(field in data.dict() for field in ["user_name", "first_name", "last_name", "email", "roles"]):
                is_keycloak_update_needed = True
                response = await update_user_in_keycloak(
                    user.keycloak_uid,
                    user.user_name,
                    user.first_name,
                    user.last_name,
                    user.email,
                    user.roles,
                )

                if response.get("status") != "success":
                    session.abort_transaction()
                    session.end_session()
                    return {
                        "status": "failed",
                        "message": f"Keycloak update error: {response.get('message', 'Unknown error')}"
                    }

            session.commit_transaction()
            return {
                "status": "success",
                "message": f"User updated successfully. {'A new login token will be needed.' if is_keycloak_update_needed else ''}"
            }

        except Exception:
            session.abort_transaction()
            raise
        finally:
            session.end_session()

    @exception_handler
    async def delete_user(self, data) -> dict:
        """
        Delete a user from the database and from Keycloak.

        Args:
            data: An object containing the user_id of the user to delete.

        Returns:
            dict: A dictionary containing the status and message of the operation.
        """
        # No transaction needed for a simple deletion unless required by business logic
        user_id = data.user_id
        user = User.objects(id=user_id).first()

        if not user:
            self.logger.error(f"User not found: {user_id}")
            return {"status": "failed", "message": "User not found"}

        keycloak_response = await delete_user_from_keycloak(user.keycloak_uid)
        if keycloak_response.get('status') != 'success':
            self.logger.error(f"Error from Keycloak: {str(keycloak_response['message'])}")
            # Adjusted message to match test expectation:
            return {'status': 'failed', 'message': "Keycloak error"}

        user.delete()
        self.logger.info(f"User deleted: {user_id}")
        return {"status": "success", "message": "User deleted successfully"}

    @exception_handler
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
                self.logger.error("Unauthorized access")
                return {"status": "failed", "message": "Unauthorized access"}

        # No transaction needed for a simple read
        if request_user and not data.user_id:
            user_id = request_user.get("id")
        else:
            user_id = data.user_id
        user = User.objects(id=user_id).first()
        if not user:
            self.logger.error(f"User not found: {user_id}")
            return {"status": "failed", "message": "User not found"}

        user_data = {
            "id": str(user.id),
            "user_name": user.user_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.roles,
            "email": user.email,
            "creation_date": user.creation_date,
        }
        return {"status": "success", "data": user_data}

    @exception_handler
    async def get_user_by_keycloak_uid(self, data) -> dict:
        """
        Retrieve a user's information from the database using their Keycloak UID.

        Args:
            data: An object containing the keycloak_uid of the user.

        Returns:
            dict: A dictionary containing the status and user data if found.
        """
        # No transaction needed for a simple read
        keycloak_uid = data.keycloak_uid
        user = User.objects(keycloak_uid=keycloak_uid).first()
        if not user:
            self.logger.error(f"User not found: {keycloak_uid}")
            return {"status": "failed", "message": "User not found"}

        user_dict = user.to_mongo().to_dict()
        user_dict.pop("keycloak_uid", None)  # Remove for security reasons
        user_dict["id"] = str(user_dict["_id"])
        del user_dict["_id"]
        user_dict.pop("_cls", None)
        return {"status": "success", "data": user_dict}


manager = UserManager()
