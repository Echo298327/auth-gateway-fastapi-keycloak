from pydantic import Field, EmailStr
from datetime import datetime
from beanie import Document
from pymongo import IndexModel, ASCENDING, DESCENDING
from typing import List, Optional
from uuid import UUID


class User(Document):
    keycloak_uid: Optional[UUID] = Field(default=None, description="Keycloak user ID (UUID)")
    user_name: str = Field(..., description="Username (automatically converted to lowercase)")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Email address")
    roles: List[str] = Field(..., description="List of role IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="System creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("user_name", ASCENDING)], unique=True, name="idx_user_name"),
            IndexModel([("email", ASCENDING)], unique=True, name="idx_email"),
            IndexModel([("keycloak_uid", ASCENDING)], unique=True, sparse=True, name="idx_keycloak_uid"),
            IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
        ]
