from pydantic_settings import BaseSettings
from schemas import AuthConfigurations
from typing import ClassVar
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # app settings
    PORT: int = int(os.getenv("GATEWAY_PORT", 8080))
    HOST: str = os.getenv("GATEWAY_HOST", "0.0.0.0")

    # keycloak settings
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:9002")
    REALM: str = os.getenv("REALM", "templateRealm")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "templateApp")
    AUTHORIZATION_URL: str = os.getenv("AUTHORIZATION_URL")
    TOKEN_URL: str = os.getenv("TOKEN_URL")

    SERVICE_MAP: ClassVar[dict] = {
        "user": os.getenv("USERS_URL"),
    }

    @classmethod
    def load_keycloak_credentials(cls) -> AuthConfigurations:
        return AuthConfigurations(
            server_url=cls.SERVER_URL,
            realm=cls.REALM,
            client_id=cls.CLIENT_ID,
            authorization_url=cls.AUTHORIZATION_URL,
            token_url=cls.TOKEN_URL,
            client_secret=None,
        )


settings = Settings()

