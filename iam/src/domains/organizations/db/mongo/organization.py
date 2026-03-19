"""
Database operations for organizations collection.
"""

from domains.organizations.models import Organization
from domains.users.models import User
from typing import Optional, List
from bson import ObjectId
from datetime import datetime, timezone


async def find_by_id(org_id: str) -> Optional[Organization]:
    return await Organization.find_one({"_id": ObjectId(org_id)})


async def find_by_slug(slug: str) -> Optional[Organization]:
    return await Organization.find_one({"slug": slug})


async def find_by_keycloak_org_id(keycloak_org_id: str) -> Optional[Organization]:
    return await Organization.find_one({"keycloak_org_id": keycloak_org_id})


async def find_default_org() -> Optional[Organization]:
    return await Organization.find_one({"is_default": True})


async def create_organization(
    name: str,
    slug: str,
    description: Optional[str] = None,
    domains: Optional[List[str]] = None,
    is_default: bool = False,
    keycloak_org_id: Optional[str] = None,
) -> Organization:
    org = Organization(
        name=name,
        slug=slug,
        description=description,
        domains=domains or [],
        is_default=is_default,
        keycloak_org_id=keycloak_org_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return await org.insert()


async def update_organization(org: Organization, **kwargs) -> Organization:
    for field, value in kwargs.items():
        if value is not None and hasattr(org, field):
            setattr(org, field, value)
    org.updated_at = datetime.now(timezone.utc)
    await org.save()
    return org


async def delete_organization(org_id: str) -> bool:
    org = await find_by_id(org_id)
    if not org:
        return False
    await org.delete()
    return True


async def get_all_organizations(limit: Optional[int] = None, skip: Optional[int] = None) -> List[Organization]:
    query = Organization.find()
    if skip:
        query = query.skip(skip)
    if limit:
        query = query.limit(limit)
    return await query.to_list()


async def get_org_users(org_id: str) -> List[User]:
    return await User.find({"organizations": org_id}).to_list()


async def slug_exists(slug: str, exclude_org_id: Optional[str] = None) -> bool:
    query = {"slug": slug}
    if exclude_org_id:
        query["_id"] = {"$ne": ObjectId(exclude_org_id)}
    return await Organization.find_one(query) is not None


async def get_users_without_org() -> List[User]:
    """Get all users with empty organizations list (for backfill)."""
    return await User.find({"organizations": {"$size": 0}}).to_list()
