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
    PORT: int = int(os.getenv("USERS_PORT", 8080))
    HOST: str = os.getenv("USERS_HOST", "0.0.0.0")
    # email settings
    APP_EMAIL: str = os.getenv("APP_EMAIL", "email")
    APP_PASSWORD: str = os.getenv("APP_PASSWORD", "password")

    def connect_db(self):
        connect(host=self.MONGO_CONNECTION_STRING, db=self.DB_NAME)


settings = Settings()
