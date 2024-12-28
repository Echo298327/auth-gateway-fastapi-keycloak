from pydantic_settings import BaseSettings, SettingsConfigDict
from auth_gateway_serverkit.logger import init_logger
from pydantic import Field
from mongoengine import connect
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

logger = init_logger("users.config")


class Settings(BaseSettings):
    # Database settings
    MONGO_CONNECTION_STRING: str
    DB_NAME: str

    # App settings
    PORT: int = Field(alias="USERS_PORT")
    HOST: str = Field(alias="USERS_HOST")

    # Email settings
    APP_EMAIL: str
    APP_PASSWORD: str

    # System admin settings
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

    # Load environment variables from .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow"  # This allows extra fields from environment variables
    )

    def connect_db(self):
        """Connect to the MongoDB database using MongoEngine."""
        connect(host=self.MONGO_CONNECTION_STRING, db=self.DB_NAME)

    def get_db_client(self) -> MongoClient:
        """
        Get a MongoDB client instance for direct session management or transactional operations.
        """
        return MongoClient(self.MONGO_CONNECTION_STRING)


try:
    settings = Settings()
except ValueError as e:
    logger.error(f"Error loading settings: {e}")
    import sys
    sys.exit(1)
