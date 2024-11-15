from pydantic_settings import BaseSettings
from typing import ClassVar
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # app settings
    PORT: int = int(os.getenv("GATEWAY_PORT", 8080))
    HOST: str = os.getenv("GATEWAY_HOST", "0.0.0.0")

    SERVICE_MAP: ClassVar[dict] = {
        "user": os.getenv("USERS_URL"),
    }


settings = Settings()
