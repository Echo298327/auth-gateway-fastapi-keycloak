import re
from auth_gateway_serverkit.logger import init_logger
from auth_gateway_serverkit.keycloak.organization import (
    create_organization as kc_create_org,
    update_organization as kc_update_org,
    delete_organization as kc_delete_org,
    add_member_to_organization as kc_add_member,
    remove_member_from_organization as kc_remove_member,
)
from core.config import settings
from domains.organizations.db.mongo.organization import (
    find_by_id,
    find_by_slug,
    find_default_org,
    create_organization,
    update_organization,
    delete_organization,
    get_all_organizations,
    get_org_users,
    slug_exists,
    get_users_without_org,
)
from domains.users.db.mongo.user import find_by_user_id, update_user
from utils.admin import is_admins
from utils.exception_handler import exception_handler


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


class OrganizationManager:
    def __init__(self):
        self.logger = init_logger(__name__)

    @exception_handler("error creating organization")
    async def create_org(self, data) -> dict:
        name = data.name.strip()
        slug = _slugify(name)

        if await slug_exists(slug):
            raise Exception(f"Organization with slug '{slug}' already exists")

        kc_result = await kc_create_org(name, description=data.description, domains=data.domains)
        keycloak_org_id = kc_result["id"] if kc_result else None

        org = await create_organization(
            name=name,
            slug=slug,
            description=data.description,
            domains=data.domains,
            keycloak_org_id=keycloak_org_id,
        )

        self.logger.info(f"Organization created: {org.id} (slug={slug})")
        return {
            "status": "success",
            "org_id": str(org.id),
            "message": "Organization created successfully",
        }

    @exception_handler("error updating organization")
    async def update_org(self, data) -> dict:
        org = await find_by_id(data.org_id)
        if not org:
            raise Exception(f"Organization not found: {data.org_id}")

        update_fields = {}
        if data.name is not None:
            new_slug = _slugify(data.name)
            if new_slug != org.slug and await slug_exists(new_slug, exclude_org_id=data.org_id):
                raise Exception(f"Organization with slug '{new_slug}' already exists")
            update_fields["name"] = data.name.strip()
            update_fields["slug"] = new_slug
        if data.description is not None:
            update_fields["description"] = data.description
        if data.domains is not None:
            update_fields["domains"] = data.domains
        if data.settings is not None:
            update_fields["settings"] = data.settings

        await update_organization(org, **update_fields)

        if org.keycloak_org_id:
            kc_data = {}
            if data.name is not None:
                kc_data["name"] = data.name.strip()
            if data.description is not None:
                kc_data["description"] = data.description
            if data.domains is not None:
                kc_data["domains"] = [{"name": d, "verified": True} for d in data.domains]
            if kc_data:
                await kc_update_org(org.keycloak_org_id, kc_data)

        return {"status": "success", "message": "Organization updated successfully"}

    @exception_handler("error deleting organization")
    async def delete_org(self, data) -> dict:
        org = await find_by_id(data.org_id)
        if not org:
            raise Exception(f"Organization not found: {data.org_id}")
        if org.is_default:
            raise Exception("Cannot delete the default organization")

        if org.keycloak_org_id:
            await kc_delete_org(org.keycloak_org_id)

        await delete_organization(data.org_id)
        self.logger.info(f"Organization deleted: {data.org_id}")
        return {"status": "success", "message": "Organization deleted successfully"}

    @exception_handler("error getting organization")
    async def get_org(self, data) -> dict:
        if data.org_id:
            org = await find_by_id(data.org_id)
            if not org:
                raise Exception(f"Organization not found: {data.org_id}")
            return {"status": "success", "data": _org_to_dict(org)}

        orgs = await get_all_organizations()
        return {"status": "success", "data": [_org_to_dict(o) for o in orgs]}

    @exception_handler("error adding user to organization")
    async def add_user_to_org(self, data) -> dict:
        org = await find_by_id(data.org_id)
        if not org:
            raise Exception(f"Organization not found: {data.org_id}")

        user = await find_by_user_id(data.user_id)
        if not user:
            raise Exception(f"User not found: {data.user_id}")

        org_id_str = str(org.id)
        if org_id_str in user.organizations:
            return {"status": "success", "message": "User already in organization"}

        user.organizations.append(org_id_str)
        await update_user(user, organizations=user.organizations)

        if org.keycloak_org_id and user.keycloak_uid:
            await kc_add_member(org.keycloak_org_id, str(user.keycloak_uid))

        self.logger.info(f"User {data.user_id} added to organization {data.org_id}")
        return {"status": "success", "message": "User added to organization"}

    @exception_handler("error removing user from organization")
    async def remove_user_from_org(self, data) -> dict:
        org = await find_by_id(data.org_id)
        if not org:
            raise Exception(f"Organization not found: {data.org_id}")

        user = await find_by_user_id(data.user_id)
        if not user:
            raise Exception(f"User not found: {data.user_id}")

        org_id_str = str(org.id)
        if org_id_str not in user.organizations:
            return {"status": "success", "message": "User not in organization"}

        user.organizations.remove(org_id_str)
        await update_user(user, organizations=user.organizations)

        if org.keycloak_org_id and user.keycloak_uid:
            await kc_remove_member(org.keycloak_org_id, str(user.keycloak_uid))

        self.logger.info(f"User {data.user_id} removed from organization {data.org_id}")
        return {"status": "success", "message": "User removed from organization"}

    @exception_handler("error getting organization members")
    async def get_members(self, data) -> dict:
        org = await find_by_id(data.org_id)
        if not org:
            raise Exception(f"Organization not found: {data.org_id}")

        users = await get_org_users(str(org.id))
        members = [
            {
                "id": str(u.id),
                "user_name": u.user_name,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
            }
            for u in users
        ]
        return {"status": "success", "data": members}

    async def create_default_organization(self) -> str:
        """
        Create the default organization if it doesn't exist.
        Backfill existing users (except systemAdmin) that have no orgs.
        Returns the default org ID string.
        """
        existing = await find_default_org()
        if existing:
            self.logger.info(f"Default organization already exists: {existing.id}")
            default_org_id = str(existing.id)
        else:
            kc_result = await kc_create_org("Default", description="Default organization")
            keycloak_org_id = kc_result["id"] if kc_result else None

            org = await create_organization(
                name="Default",
                slug="default",
                description="Default organization",
                is_default=True,
                keycloak_org_id=keycloak_org_id,
            )
            default_org_id = str(org.id)
            self.logger.info(f"Default organization created: {default_org_id}")

        system_admin_id = await settings.get_system_admin_id()
        users_without_org = await get_users_without_org()
        backfilled = 0
        for user in users_without_org:
            if str(user.id) == system_admin_id:
                continue
            user.organizations.append(default_org_id)
            await update_user(user, organizations=user.organizations)

            existing_org = await find_by_id(default_org_id)
            if existing_org and existing_org.keycloak_org_id and user.keycloak_uid:
                await kc_add_member(existing_org.keycloak_org_id, str(user.keycloak_uid))
            backfilled += 1

        if backfilled:
            self.logger.info(f"Backfilled {backfilled} users into default organization")

        return default_org_id


def _org_to_dict(org: "Organization") -> dict:
    return {
        "id": str(org.id),
        "keycloak_org_id": org.keycloak_org_id,
        "name": org.name,
        "slug": org.slug,
        "description": org.description,
        "domains": org.domains,
        "is_default": org.is_default,
        "settings": org.settings,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
    }


manager = OrganizationManager()
