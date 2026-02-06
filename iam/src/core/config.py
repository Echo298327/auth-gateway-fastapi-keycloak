from pydantic_settings import BaseSettings, SettingsConfigDict
from auth_gateway_serverkit.logger import init_logger
from pydantic import Field
from typing import ClassVar, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
import sys

load_dotenv()

logger = init_logger("iam.config")


class Settings(BaseSettings):
    # Database settings
    MONGO_CONNECTION_STRING: str
    DB_NAME: str

    # App settings
    PORT: int = Field(alias="IAM_PORT")
    HOST: str = Field(alias="IAM_HOST")
    WORKERS: int = Field(default=1, alias="IAM_WORKERS")
    ENVIRONMENT: str = Field(default="local", alias="ENVIRONMENT")

    # Email settings
    APP_EMAIL: str
    APP_PASSWORD: str

    # System admin user info
    SYSTEM_ADMIN_USER_NAME: str
    SYSTEM_ADMIN_FIRST_NAME: str
    SYSTEM_ADMIN_LAST_NAME: str
    SYSTEM_ADMIN_EMAIL: str
    SYSTEM_ADMIN_PASSWORD: str

    # Keycloak settings (KEYCLOAK_CONFIG_VERSION in code; bump to force full Keycloak authz sync)
    KEYCLOAK_CONFIG_VERSION: str = "0.0.1"
    SERVER_URL: str
    REALM: str
    CLIENT_ID: str
    SCOPE: str
    AUTHORIZATION_URL: str
    TOKEN_URL: str
    KC_BOOTSTRAP_ADMIN_USERNAME: str
    KC_BOOTSTRAP_ADMIN_PASSWORD: str

    # Static class var (shared across instances)
    SYSTEM_ADMIN_ID: ClassVar[Optional[str]] = None

    _system_admin_role_id: Optional[str] = None
    _admin_role_id: Optional[str] = None

    # Load environment variables from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"  # Accept extra env vars
    )

    async def init_db(self):
        """Initialize the MongoDB database using Beanie."""
        from domains.users.models import User
        from domains.service_versions.models import ServiceVersion
        
        client = AsyncIOMotorClient(self.MONGO_CONNECTION_STRING)
        database = client[self.DB_NAME]
        
        await init_beanie(database=database, document_models=[User, ServiceVersion])
        return client

    def get_motor_client(self) -> AsyncIOMotorClient:
        """Get an async MongoDB client instance."""
        return AsyncIOMotorClient(self.MONGO_CONNECTION_STRING)

    @property
    def reload(self) -> bool:
        """Return True if the app is running in local/dev mode."""
        return self.ENVIRONMENT == "local"

    @property
    def SYSTEM_ADMIN_ROLE_ID(self) -> Optional[str]:
        return self._system_admin_role_id

    @property
    def ADMIN_ROLE_ID(self) -> Optional[str]:
        return self._admin_role_id

    def set_system_admin_role_id(self, role_id: str):
        self._system_admin_role_id = role_id

    def set_admin_role_id(self, role_id: str):
        self._admin_role_id = role_id

    def has_system_admin_role_id(self) -> bool:
        return self._system_admin_role_id is not None

    def has_admin_role_id(self) -> bool:
        return self._admin_role_id is not None

    async def get_system_admin_id(self) -> str:
        """Fetch system admin ID (from cache or DB)."""
        if not type(self).SYSTEM_ADMIN_ID:
            logger.warning("System admin ID not set, fetching from database...")
            from utils.admin import fetch_system_admin_id
            type(self).SYSTEM_ADMIN_ID = await fetch_system_admin_id()
        return str(type(self).SYSTEM_ADMIN_ID)


# Load settings on import, with fallback error handling
try:
    settings = Settings()
except ValueError as e:
    logger.error(f"Error loading settings: {e}")
    sys.exit(1)
