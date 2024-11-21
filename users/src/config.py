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
    # keycloak settings
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:9002")
    REALM: str = os.getenv("REALM", "templateRealm")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "templateApp")
    SCOPE: str = os.getenv("SCOPE", "openid")
    AUTHORIZATION_URL: str = os.getenv("AUTHORIZATION_URL")
    TOKEN_URL: str = os.getenv("TOKEN_URL")
    ADMIN_U: str = os.getenv("ADMIN_U", "admin")
    ADMIN_P: str = os.getenv("ADMIN_P", "admin")

    def connect_db(self):
        connect(host=self.MONGO_CONNECTION_STRING, db=self.DB_NAME)


settings = Settings()
