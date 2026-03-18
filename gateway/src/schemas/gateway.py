from pydantic import BaseModel
from typing import Optional


class Login(BaseModel):
    username: str
    password: str
    totp: Optional[str] = None

    class Config:
        extra = 'forbid'


class Refresh(BaseModel):
    refresh_token: str

    class Config:
        extra = 'forbid'

