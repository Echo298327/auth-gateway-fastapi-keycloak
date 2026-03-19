from datetime import datetime, timezone
from beanie import Document
from pymongo import IndexModel, ASCENDING
from typing import List, Optional
from pydantic import Field


class Organization(Document):
    keycloak_org_id: Optional[str] = None
    name: str = Field(..., description="Display name")
    slug: str = Field(..., description="URL-friendly unique identifier")
    description: Optional[str] = None
    domains: List[str] = Field(default_factory=list, description="Email domains for auto-assignment")
    is_default: bool = Field(default=False, description="Only one org can be default")
    settings: dict = Field(default_factory=dict, description="Extensible org-level settings")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "organizations"
        indexes = [
            IndexModel([("slug", ASCENDING)], unique=True, name="idx_slug"),
            IndexModel([("keycloak_org_id", ASCENDING)], unique=True, sparse=True, name="idx_keycloak_org_id"),
            IndexModel([("is_default", ASCENDING)], name="idx_is_default"),
        ]
