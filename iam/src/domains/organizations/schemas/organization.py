from pydantic import BaseModel, Field
from typing import Optional, List


class CreateOrganization(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    domains: Optional[List[str]] = None

    class Config:
        extra = "forbid"


class UpdateOrganization(BaseModel):
    org_id: str
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    domains: Optional[List[str]] = None
    settings: Optional[dict] = None

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
