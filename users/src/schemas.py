from pydantic import BaseModel, EmailStr, Extra
from typing import Optional


class CreateUser(BaseModel):
    user_name: str
    first_name: str
    last_name: str
    role_id: str
    email: EmailStr

    class Config:
        extra = Extra.forbid


class UpdateUser(BaseModel):
    user_id: str
    first_name: Optional[str] = None
    user_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[str] = None

    class Config:
        extra = Extra.forbid


class DeleteUser(BaseModel):
    user_id: str

    class Config:
        extra = Extra.forbid


class GetUser(BaseModel):
    user_id: str

    class Config:
        extra = Extra.forbid
