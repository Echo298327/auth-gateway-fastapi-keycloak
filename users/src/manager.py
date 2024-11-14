import time
from mongoengine.errors import DoesNotExist, ValidationError

try:
    from config import settings
    from password_gen import generate_password
    from email_handler import send_password_email
    from mongo_models import User
    from logger import init_logger
except ImportError:
    from .config import settings
    from .password_gen import generate_password
    from .email_handler import send_password_email
    from .mongo_models import User
    from .logger import init_logger


logger = init_logger("user.manager")


async def create_user(data):
    try:
        user_data = data.dict()
        user_name = user_data.get("user_name")
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")
        email = user_data.get("email")

        if User.objects(user_name__iexact=user_name.lower()).first():
            return {"status": "failed", "message": "User name already exists"}

        password = generate_password()
        # response = await add_user_to_keycloak(user_name, first_name, last_name, email, password)
        # if response.get('status') != 'success':
        #     logger.error(f"Failed to create user in Keycloak: {response.get('message')}")
        #     return response
        #
        # if not response.get('keycloakUserId'):
        #     logger.error("Failed to get keycloak user id")
        #     return {"status": "failed", "message": "Failed to get keycloak user id"}
        # keycloak_uid = response.get('keycloakUserId')

        user = User(
            user_name=user_name,
            first_name=first_name,
            last_name=last_name,
            role_id=user_data.get('role_id'),
            email=email,
            keycloak_uid='keycloak_uid',
            creation_date=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        user.save()

        if not User.objects(id=user.id).first():
            logger.error("Failed to verify the saved user.")
            return {"status": "failed", "message": "Failed to save user."}

        send_password_email(user.first_name, user.email, user.user_name, password)
        return {"status": "success", "user_id": str(user.id), "message": "User created successfully"}

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return {"status": "failed", "message": "Internal Server Error"}


async def update_user(data):
    try:
        user_data = data.dict()
        user_id = user_data.get("user_id")
        user_name = user_data.get("user_name")
        del user_data["user_id"]

        user = User.objects(id=user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "failed", "message": "User not found"}

        if user_data.get("user_name"):
            if User.objects(user_name__iexact=user_name.lower()).first():
                return {"status": "failed", "message": "User name already exists"}

        update_data = {key: value for key, value in user_data.items() if value is not None}
        User.objects(id=user.id).update(**update_data)
        logger.info(f"User updated: {user_id}")
        return {"status": "success", "message": "User updated successfully"}

    except ValidationError as ve:
        logger.error(f"Validation error while updating user: {str(ve)}")
        return {"status": "failed", "message": str(ve)}
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return {"status": "failed", "message": "Internal Server Error"}


async def delete_user(data):
    try:
        user_data = data.dict()
        user_id = user_data.get("user_id")
        user = User.objects(id=user_id).first()

        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "failed", "message": "User not found"}

        # keycloak_response = await delete_user_from_keycloak(user.keycloak_uid)
        # if keycloak_response.get('status') != 'success':
        #     logger.error(f"Error from Keycloak: {str(keycloak_response['message'])}")
        #     return {'status': 'fail', 'message': str(keycloak_response['message'])}

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


async def get_user(data):
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
            "role_id": user.role_id,
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
