import time
from mongoengine.errors import DoesNotExist, ValidationError
from auth_gateway_serverkit.logger import init_logger
from auth_gateway_serverkit.password import generate_password
from auth_gateway_serverkit.email import send_password_email

try:
    from config import settings
    from mongo_models import User
    from schemas import AllowedRoles
    from keycloak_manager import add_user_to_keycloak, update_user_in_keycloak, delete_user_from_keycloak
except ImportError:
    from .config import settings
    from .mongo_models import User
    from .schemas import AllowedRoles
    from .keycloak_manager import add_user_to_keycloak, update_user_in_keycloak, delete_user_from_keycloak


logger = init_logger("user.manager")


async def create_system_admin() -> bool:
    try:
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
            logger.error(f"Failed to create system admin in Keycloak: {response.get('message')}")
            return False

        if not response.get('keycloakUserId'):
            logger.error("Failed to get keycloak user id")
            return False
        keycloak_uid = response.get('keycloakUserId')

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
            logger.error("Failed to verify the saved system admin.")
            return False

        logger.info(f"System admin created: {user.id}")
        return True

    except Exception as e:
        logger.error(f"Error creating system admin: {str(e)}")
        return False


async def create_user(data) -> dict:
    try:
        user_data = data.dict()
        user_name = user_data.get("user_name")
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")
        email = user_data.get("email")
        roles = user_data.get("roles")

        # Convert Enum instances to their string values
        roles = [role.value if isinstance(role, AllowedRoles) else role for role in roles]

        if User.objects(user_name__iexact=user_name.lower()).first():
            return {"status": "failed", "message": "User name already exists"}

        password = generate_password()
        response = await add_user_to_keycloak(user_name, first_name, last_name, email, password, roles)
        if response.get('status') != 'success':
            logger.error(f"Failed to create user in Keycloak: {response.get('message')}")
            return response

        if not response.get('keycloakUserId'):
            logger.error("Failed to get keycloak user id")
            return {"status": "failed", "message": "Failed to get keycloak user id"}
        keycloak_uid = response.get('keycloakUserId')

        user = User(
            user_name=user_name,
            first_name=first_name,
            last_name=last_name,
            roles=roles,
            email=email,
            keycloak_uid=keycloak_uid,
            creation_date=time.strftime("%d-%m-%Y"),
        )
        user.save()

        if not User.objects(id=user.id).first():
            logger.error("Failed to verify the saved user.")
            return {"status": "failed", "message": "Failed to save user."}

        # send_password_email(settings.APP_EMAIL, settings.APP_PASSWORD, user.first_name, user.email, user.user_name, password)
        logger.info(f"User created: {user.id}")
        return {"status": "success", "user_id": str(user.id), "message": "User created successfully"}

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return {"status": "failed", "message": "Internal Server Error"}


async def update_user(data) -> dict:
    try:
        user_data = data.dict()
        user_id = user_data.get("user_id")
        user_name = user_data.get("user_name",None)
        roles = user_data.get("roles", None)
        del user_data["user_id"]

        # Convert Enum instances to their string values
        roles = [role.value if isinstance(role, AllowedRoles) else role for role in roles]

        if all(value is None for value in user_data.values()):
            return {"status": "failed", "message": "No data to update"}

        user = User.objects(id=user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "failed", "message": "User not found"}

        if user_data.get("user_name"):
            if User.objects(user_name__iexact=user_name.lower()).first():
                return {"status": "failed", "message": "User name already exists"}

        update_data = {key: value for key, value in user_data.items() if value is not None}
        User.objects(id=user.id).update(**update_data)

        response = await update_user_in_keycloak(
            user.keycloak_uid,
            user_name,
            user.first_name,
            user.last_name,
            user.email,
            roles,
        )
        if response.get('status') != 'success':
            logger.error(f"Error from Keycloak: {str(response['message'])}")
            return {'status': 'fail', 'message': str(response['message'])}

        logger.info(f"User updated: {user_id}")
        return {"status": "success", "message": "User updated successfully"}

    except ValidationError as ve:
        logger.error(f"Validation error while updating user: {str(ve)}")
        return {"status": "failed", "message": str(ve)}
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return {"status": "failed", "message": "Internal Server Error"}


async def delete_user(data) -> dict:
    try:
        user_data = data.dict()
        user_id = user_data.get("user_id")
        user = User.objects(id=user_id).first()

        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "failed", "message": "User not found"}

        keycloak_response = await delete_user_from_keycloak(user.keycloak_uid)
        if keycloak_response.get('status') != 'success':
            logger.error(f"Error from Keycloak: {str(keycloak_response['message'])}")
            return {'status': 'fail', 'message': str(keycloak_response['message'])}

        user.delete()
        logger.info(f"User deleted: {user_id}")
        return {"status": "success", "message": "User deleted successfully"}

    except ValidationError as ve:
        logger.error(f"Validation error while deleting user: {str(ve)}")
        return {"status": "failed", "message": str(ve)}
    except DoesNotExist:
        logger.error(f"User not found")
        return {"status": "failed", "message": "User not found"}
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return {"status": "failed", "message": "Internal Server Error"}


async def get_user(data) -> dict:
    try:
        user_data = data.dict()
        user_id = user_data.get("user_id")
        user = User.objects(id=user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "failed", "message": "User not found"}

        data = {
            "id": str(user.id),
            "user_name": user.user_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.roles,
            "email": user.email,
            "keycloak_uid": user.keycloak_uid,
            "creation_date": user.creation_date,
        }

        return {"status": "success", "data": data}

    except DoesNotExist:
        logger.error(f"User not found")
        return {"status": "failed", "message": "User not found"}
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        return {"status": "failed", "message": "Internal Server Error"}


async def get_user_by_keycloak_uid(data) -> dict:
    try:
        user_data = data.dict()
        keycloak_uid = user_data.get("keycloak_uid")
        user = User.objects(keycloak_uid=keycloak_uid).first()
        if not user:
            logger.error(f"User not found: {keycloak_uid}")
            return {"status": "failed", "message": "User not found"}

        data = {
            "id": str(user.id),
            "user_name": user.user_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.roles,
            "email": user.email,
            "keycloak_uid": user.keycloak_uid,
            "creation_date": user.creation_date,
        }

        return {"status": "success", "data": data}

    except DoesNotExist:
        logger.error(f"User not found")
        return {"status": "failed", "message": "User not found"}
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        return {"status": "failed", "message": "Internal Server Error"}
