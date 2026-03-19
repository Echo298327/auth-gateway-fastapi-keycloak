from pydantic import Field
from datetime import datetime, timezone
from beanie import Document
from pymongo import IndexModel, ASCENDING


class ServiceVersion(Document):
    service: str = Field(..., description="Service identifier (e.g. keycloak)")
    version: str = Field(default="0.0.0", description="Current config version")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    class Settings:
        name = "service_versions"
        indexes = [
            IndexModel([("service", ASCENDING)], unique=True, name="idx_service"),
        ]
