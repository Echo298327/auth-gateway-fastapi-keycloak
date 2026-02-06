"""Database operations for service_versions collection."""

from domains.service_versions.models import ServiceVersion
from datetime import datetime

DEFAULT_VERSION = "0.0.0"
KEYCLOAK_KEY = "keycloak"


async def get_version(key: str = KEYCLOAK_KEY) -> str:
    """
    Get the stored version for a service key.

    Args:
        key: Service identifier (e.g. keycloak)

    Returns:
        Stored version string, or DEFAULT_VERSION if not found
    """
    doc = await ServiceVersion.find_one({"service": key})
    return doc.version if doc else DEFAULT_VERSION


async def set_version(key: str, version: str) -> ServiceVersion:
    """
    Create or update the version for a service key.

    Args:
        key: Service identifier (e.g. keycloak)
        version: Version string to store

    Returns:
        Updated ServiceVersion document
    """
    doc = await ServiceVersion.find_one({"service": key})
    if doc:
        doc.version = version
        doc.updated_at = datetime.utcnow()
        await doc.save()
        return doc
    doc = ServiceVersion(service=key, version=version)
    return await doc.insert()
