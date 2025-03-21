from pydantic_settings import BaseSettings, SettingsConfigDict
from auth_gateway_serverkit.logger import init_logger
import auth_gateway_serverkit.http_client as http
from pydantic import Field
from typing import ClassVar, Optional
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

    SYSTEM_ADMIN_ID: ClassVar[Optional[str]] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SERVICE_MAP = {
            "user": self.USERS_URL,
        }

    async def get_system_admin_id(self):
        if not type(self).SYSTEM_ADMIN_ID:
            type(self).SYSTEM_ADMIN_ID = await http.get(url=self.SERVICE_MAP.get("user") + "/get_sys_id")
            logger.info(f"System admin ID: {type(self).SYSTEM_ADMIN_ID}")
        return type(self).SYSTEM_ADMIN_ID


try:
    settings = Settings()
except ValueError as e:
    logger.error(f"Error loading settings: {e}")
    import sys
    sys.exit(1)
