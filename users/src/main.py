from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.config import settings
from auth_gateway_serverkit.keycloak.initializer import initialize_keycloak_server
from auth_gateway_serverkit.logger import init_logger
from utils.admin import set_admins_role_ids
from services.user_manager import manager
from api import init_routes


logger = init_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    is_set_admins_role_ids = False
    try:
        await settings.init_db()
        # Set cleanup_and_build=True for fresh deployment
        is_initialized = await initialize_keycloak_server(cleanup_and_build=True)
        if not is_initialized:
            raise Exception("Failed to initialize Keycloak server")
        is_system_admin_created = await manager.create_system_admin()
        if not is_system_admin_created:
            raise Exception("Failed to create system admin")
        if not settings.has_system_admin_role_id() or not settings.has_admin_role_id():
            is_set_admins_role_ids = await set_admins_role_ids()
        if not is_set_admins_role_ids:
            raise Exception("Failed to set admin role IDs")

        yield  # Application startup complete
        logger.info("Application shutdown...")
    except Exception as e:
        logger.error(f"Error during lifespan management: {e}")
        raise e


app = FastAPI( title="Users Service", lifespan=lifespan)
init_routes(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.reload
    )
