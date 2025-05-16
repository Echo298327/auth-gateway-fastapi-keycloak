from pydantic import BaseModel, Extra


class Login(BaseModel):
    username: str
    password: str

    class Config:
        extra = 'forbid'

