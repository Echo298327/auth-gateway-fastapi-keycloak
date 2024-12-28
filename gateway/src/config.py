from pydantic_settings import BaseSettings, SettingsConfigDict
from auth_gateway_serverkit.logger import init_logger
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

logger = init_logger("gateway.config")


class Settings(BaseSettings):
    # app settings
    PORT: int = Field(alias="GATEWAY_PORT")
    HOST: str = Field(alias="USERS_HOST")

    # environment-specific URLs
    USERS_URL: str

    SERVICE_MAP: dict = {}

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SERVICE_MAP = {
            "user": self.USERS_URL,
        }


try:
    settings = Settings()
except ValueError as e:
    logger.error(f"Error loading settings: {e}")
    import sys
    sys.exit(1)
