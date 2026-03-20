from datetime import datetime, timezone
from uuid import UUID
from beanie import Document
from pymongo import IndexModel, ASCENDING
from typing import List, Optional
from pydantic import Field


class Organization(Document):
    id: UUID = Field(default=None, description="Keycloak organization UUID (used as _id)")
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
            IndexModel([("is_default", ASCENDING)], name="idx_is_default"),
        ]
