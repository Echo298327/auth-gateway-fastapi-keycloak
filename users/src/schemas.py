from pydantic import BaseModel, EmailStr, Extra
from typing import Optional, List
from enum import Enum


class AllowedRoles(str, Enum):
    user = "user"
    admin = "admin"


class CreateUser(BaseModel):
    user_name: str
    first_name: str
    last_name: str
    roles: List[AllowedRoles]
    email: EmailStr


class UpdateUser(BaseModel):
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    roles: Optional[List[AllowedRoles]] = None

    class Config:
        extra = Extra.forbid


class DeleteUser(BaseModel):
    user_id: str

    class Config:
        extra = Extra.forbid


class GetUser(BaseModel):
    user_id: Optional[str] = None

    class Config:
        extra = Extra.forbid


class GetUserByKeycloakUid(BaseModel):
    keycloak_uid: str

    class Config:
        extra = Extra.forbid