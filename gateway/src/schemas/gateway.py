from pydantic import BaseModel, Field
from typing import Optional


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=1, max_length=256)
    totp: Optional[str] = Field(default=None, min_length=6, max_length=8)

    class Config:
        extra = 'forbid'


class Refresh(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)

    class Config:
        extra = 'forbid'
