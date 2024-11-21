from .schemas import AuthConfigurations
import os


class Settings:
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:9002")
    REALM: str = os.getenv("REALM", "templateRealm")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "templateApp")
    SCOPE: str = os.getenv("SCOPE", "openid")
    AUTHORIZATION_URL: str = os.getenv("AUTHORIZATION_URL")
    TOKEN_URL: str = os.getenv("TOKEN_URL")
    ADMIN_U: str = os.getenv("ADMIN_U", "admin")
    ADMIN_P: str = os.getenv("ADMIN_P", "admin")
    CLIENT_SECRET: str = None

    @classmethod
    def load_keycloak_credentials(cls) -> AuthConfigurations:
        return AuthConfigurations(
            server_url=cls.SERVER_URL,
            realm=cls.REALM,
            client_id=cls.CLIENT_ID,
            client_secret=None,
            authorization_url=cls.AUTHORIZATION_URL,
            token_url=cls.TOKEN_URL,
        )


auth_settings = Settings()
