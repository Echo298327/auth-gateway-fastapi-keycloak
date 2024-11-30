from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from mongoengine import connect
import os

load_dotenv()


class Settings(BaseSettings):
    # database
    MONGO_CONNECTION_STRING: str = os.getenv("CONNECTION_STRING", "mongodb://localhost:27017/")
    DB_NAME: str = os.getenv("DB_NAME", "inventory")

    # app settings
    PORT: int = int(os.getenv("USERS_PORT", 8081))
    HOST: str = os.getenv("USERS_HOST", "0.0.0.0")

    # email settings
    APP_EMAIL: str = os.getenv("APP_EMAIL", "email")
    APP_PASSWORD: str = os.getenv("APP_PASSWORD", "password")

    # system admin settings
    SYSTEM_ADMIN_USER_NAME: str = os.getenv("SYSTEM_ADMIN_USER_NAME")
    SYSTEM_ADMIN_FIRST_NAME: str = os.getenv("SYSTEM_ADMIN_FIRST_NAME")
    SYSTEM_ADMIN_LAST_NAME: str = os.getenv("SYSTEM_ADMIN_LAST_NAME")
    SYSTEM_ADMIN_EMAIL: str = os.getenv("SYSTEM_ADMIN_EMAIL")
    SYSTEM_ADMIN_PASSWORD: str = os.getenv("SYSTEM_ADMIN_PASSWORD")

    # keycloak settings
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:9002")
    REALM: str = os.getenv("REALM", "templateRealm")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "templateApp")
    SCOPE: str = os.getenv("SCOPE", "openid")
    AUTHORIZATION_URL: str = os.getenv("AUTHORIZATION_URL")
    TOKEN_URL: str = os.getenv("TOKEN_URL")
    KEYCLOAK_USER: str = os.getenv("KEYCLOAK_USER", "admin")
    KEYCLOAK_PASSWORD: str = os.getenv("KEYCLOAK_PASSWORD", "admin")

    def connect_db(self):
        connect(host=self.MONGO_CONNECTION_STRING, db=self.DB_NAME)


settings = Settings()
