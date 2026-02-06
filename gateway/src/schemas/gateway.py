from pydantic import BaseModel


class Login(BaseModel):
    username: str
    password: str

    class Config:
        extra = 'forbid'


class Refresh(BaseModel):
    refresh_token: str

    class Config:
        extra = 'forbid'

