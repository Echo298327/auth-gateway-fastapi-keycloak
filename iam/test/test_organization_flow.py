"""
Organization flow tests — positive and negative scenarios for
create, update, delete, get, add_user, remove_user, and members.
"""

import pytest
from uuid import UUID
from unittest.mock import AsyncMock, patch, MagicMock
from types import SimpleNamespace

from helpers import ORG_A_ID, ORG_B_ID

MODULE = "domains.organizations.services.organization_manager"


def _fake_org(org_id=ORG_A_ID, name="test-org", slug="test-org",
              is_default=False, description=None, domains=None):
    org = MagicMock()
    org.id = UUID(org_id)
    org.name = name
    org.slug = slug
    org.is_default = is_default
    org.description = description
    org.domains = domains or []
    org.settings = {}
    org.created_at = None
    org.updated_at = None
    return org


def _fake_user(user_id="user-1", organizations=None, keycloak_uid="kc-uid-1"):
    user = MagicMock()
    user.id = user_id
    user.user_name = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.email = "test@example.com"
    user.organizations = organizations or []
    user.keycloak_uid = keycloak_uid
    return user


# ── CREATE ──────────────────────────────────────────────────────────

class TestCreateOrg:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.kc_create_org", new_callable=AsyncMock)
    @patch(f"{MODULE}.create_organization", new_callable=AsyncMock)
    @patch(f"{MODULE}.slug_exists", new_callable=AsyncMock, return_value=False)
    async def test_create_success(self, mock_slug, mock_create, mock_kc):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_kc.return_value = {"id": ORG_A_ID}
        mock_create.return_value = _fake_org()

        data = SimpleNamespace(name="test-org", description="desc", domains=["d.com"])
        result = await mgr.create_org(data)

        assert result["status"] == "success"
        assert result["org_id"] == ORG_A_ID
        mock_kc.assert_called_once()
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.slug_exists", new_callable=AsyncMock, return_value=True)
    async def test_create_duplicate_slug(self, mock_slug):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        data = SimpleNamespace(name="test-org", description=None, domains=None)
        result = await mgr.create_org(data)

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.kc_create_org", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.slug_exists", new_callable=AsyncMock, return_value=False)
    async def test_create_keycloak_failure(self, mock_slug, mock_kc):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        data = SimpleNamespace(name="test-org", description=None, domains=None)
        result = await mgr.create_org(data)

        assert result["status"] == "failed"


# ── UPDATE ──────────────────────────────────────────────────────────

class TestUpdateOrg:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.slug_exists", new_callable=AsyncMock, return_value=False)
    @patch(f"{MODULE}.kc_update_org", new_callable=AsyncMock)
    @patch(f"{MODULE}.update_organization", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_update_success(self, mock_find, mock_update, mock_kc, mock_slug):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org()
        data = SimpleNamespace(org_id=ORG_A_ID, name="new-name", description=None, domains=None, settings=None)
        result = await mgr.update_org(data)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock, return_value=None)
    async def test_update_not_found(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        data = SimpleNamespace(org_id="nonexistent", name=None, description=None, domains=None, settings=None)
        result = await mgr.update_org(data)

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.slug_exists", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_update_duplicate_slug(self, mock_find, mock_slug):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org()
        data = SimpleNamespace(org_id=ORG_A_ID, name="other-name", description=None, domains=None, settings=None)
        result = await mgr.update_org(data)

        assert result["status"] == "failed"


# ── DELETE ──────────────────────────────────────────────────────────

class TestDeleteOrg:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.delete_organization", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.kc_delete_org", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_delete_success(self, mock_find, mock_kc, mock_del):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org()
        data = SimpleNamespace(org_id=ORG_A_ID)
        result = await mgr.delete_org(data)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock, return_value=None)
    async def test_delete_not_found(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        data = SimpleNamespace(org_id="nonexistent")
        result = await mgr.delete_org(data)

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_delete_default_org_blocked(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(is_default=True)
        data = SimpleNamespace(org_id=ORG_A_ID)
        result = await mgr.delete_org(data)

        assert result["status"] == "failed"


# ── GET ─────────────────────────────────────────────────────────────

class TestGetOrg:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_get_by_id_success(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org()
        data = SimpleNamespace(org_id=ORG_A_ID)
        result = await mgr.get_org(data)

        assert result["status"] == "success"
        assert result["data"]["id"] == ORG_A_ID

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock, return_value=None)
    async def test_get_by_id_not_found(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        data = SimpleNamespace(org_id="nonexistent")
        result = await mgr.get_org(data)

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_all_organizations", new_callable=AsyncMock)
    async def test_get_all_success(self, mock_all):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_all.return_value = [_fake_org(), _fake_org(org_id=ORG_B_ID, name="org-b", slug="org-b")]
        data = SimpleNamespace(org_id=None)
        result = await mgr.get_org(data)

        assert result["status"] == "success"
        assert len(result["data"]) == 2


# ── ADD USER ────────────────────────────────────────────────────────

class TestAddUserToOrg:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.kc_add_member", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.update_user", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_add_user_success(self, mock_find_org, mock_find_user, mock_update, mock_kc):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find_org.return_value = _fake_org()
        mock_find_user.return_value = _fake_user(organizations=[])
        data = SimpleNamespace(org_id=ORG_A_ID, user_id="user-1")
        result = await mgr.add_user_to_org(data)

        assert result["status"] == "success"
        assert "added" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_add_user_already_member(self, mock_find_org, mock_find_user):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find_org.return_value = _fake_org()
        mock_find_user.return_value = _fake_user(organizations=[ORG_A_ID])
        data = SimpleNamespace(org_id=ORG_A_ID, user_id="user-1")
        result = await mgr.add_user_to_org(data)

        assert result["status"] == "success"
        assert "already" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock, return_value=None)
    async def test_add_user_org_not_found(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        data = SimpleNamespace(org_id="nonexistent", user_id="user-1")
        result = await mgr.add_user_to_org(data)

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_add_user_not_found(self, mock_find_org, mock_find_user):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find_org.return_value = _fake_org()
        data = SimpleNamespace(org_id=ORG_A_ID, user_id="nonexistent")
        result = await mgr.add_user_to_org(data)

        assert result["status"] == "failed"


# ── REMOVE USER ─────────────────────────────────────────────────────

class TestRemoveUserFromOrg:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.kc_remove_member", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.update_user", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_remove_user_success(self, mock_find_org, mock_find_user, mock_update, mock_kc):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find_org.return_value = _fake_org()
        mock_find_user.return_value = _fake_user(organizations=[ORG_A_ID])
        data = SimpleNamespace(org_id=ORG_A_ID, user_id="user-1")
        result = await mgr.remove_user_from_org(data)

        assert result["status"] == "success"
        assert "removed" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_remove_user_not_in_org(self, mock_find_org, mock_find_user):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find_org.return_value = _fake_org()
        mock_find_user.return_value = _fake_user(organizations=[])
        data = SimpleNamespace(org_id=ORG_A_ID, user_id="user-1")
        result = await mgr.remove_user_from_org(data)

        assert result["status"] == "success"
        assert "not in" in result["message"].lower()


# ── MEMBERS ─────────────────────────────────────────────────────────

class TestGetMembers:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_org_users", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_get_members_success(self, mock_find, mock_users):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org()
        mock_users.return_value = [_fake_user()]
        data = SimpleNamespace(org_id=ORG_A_ID)
        result = await mgr.get_members(data)

        assert result["status"] == "success"
        assert len(result["data"]) == 1
        assert result["data"][0]["user_name"] == "testuser"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_id", new_callable=AsyncMock, return_value=None)
    async def test_get_members_org_not_found(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        data = SimpleNamespace(org_id="nonexistent")
        result = await mgr.get_members(data)

        assert result["status"] == "failed"
