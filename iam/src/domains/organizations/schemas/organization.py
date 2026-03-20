import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

ORG_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]+$")


class CreateOrganization(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    domains: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not ORG_NAME_PATTERN.match(v.strip()):
            raise ValueError("Name must contain only letters, numbers, hyphens, and underscores")
        return v.strip()

    class Config:
        extra = "forbid"


class UpdateOrganization(BaseModel):
    org_id: str
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    domains: Optional[List[str]] = None
    settings: Optional[dict] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None and not ORG_NAME_PATTERN.match(v.strip()):
            raise ValueError("Name must contain only letters, numbers, hyphens, and underscores")
        return v.strip() if v else v

    class Config:
        extra = "forbid"


class DeleteOrganization(BaseModel):
    org_id: str

    class Config:
        extra = "forbid"


class GetOrganization(BaseModel):
    org_id: Optional[str] = None

    class Config:
        extra = "forbid"


class AddUserToOrg(BaseModel):
    org_id: str
    user_id: str

    class Config:
        extra = "forbid"


class RemoveUserFromOrg(BaseModel):
    org_id: str
    user_id: str

    class Config:
        extra = "forbid"
