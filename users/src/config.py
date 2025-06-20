from pydantic_settings import BaseSettings, SettingsConfigDict
from auth_gateway_serverkit.logger import init_logger
from pydantic import Field
from typing import ClassVar, Optional
from mongoengine import connect
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

load_dotenv()

logger = init_logger("users.config")


class Settings(BaseSettings):
    # Database settings
    MONGO_CONNECTION_STRING: str
    DB_NAME: str

    # App settings
    PORT: int = Field(alias="USERS_PORT")
    HOST: str = Field(alias="USERS_HOST")
    WORKERS: int = Field(default=1, alias="USERS_WORKERS")
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

    # Keycloak settings
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

    def connect_db(self):
        """Connect to the MongoDB database using MongoEngine."""
        connect(host=self.MONGO_CONNECTION_STRING, db=self.DB_NAME)

    def get_db_client(self) -> MongoClient:
        """Get a MongoDB client instance."""
        return MongoClient(self.MONGO_CONNECTION_STRING)

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

    def get_system_admin_id(self) -> str:
        """Fetch system admin ID (from cache or DB)."""
        if not type(self).SYSTEM_ADMIN_ID:
            logger.warning("System admin ID not set, fetching from database...")
            from utils import fetch_system_admin_id
            type(self).SYSTEM_ADMIN_ID = fetch_system_admin_id()
        return str(type(self).SYSTEM_ADMIN_ID)


# Load settings on import, with fallback error handling
try:
    settings = Settings()
except ValueError as e:
    logger.error(f"Error loading settings: {e}")
    sys.exit(1)
