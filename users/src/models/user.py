from pydantic import Field, EmailStr, field_validator
from datetime import datetime
from beanie import Document, Indexed
from typing import Annotated, List, Optional
from bson import ObjectId


class User(Document):
    user_name: Annotated[str, Indexed(unique=True)] = Field(..., description="Username (automatically converted to lowercase)")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    roles: List[str] = Field(..., description="List of role IDs")
    email: Annotated[EmailStr, Indexed(unique=True)] = Field(..., description="Email address")
    keycloak_uid: Annotated[Optional[str], Indexed(unique=True, sparse=True)] = Field(default=None, description="Keycloak user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="System creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "users"
