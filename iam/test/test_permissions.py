"""
Permission tests — validates org-scoped access control across all layers:
  1. admin.py utility functions (is_system_admin, check_org_scope, check_user_org_overlap)
  2. Organization manager permission enforcement
  3. User manager permission enforcement
  4. Gateway org access check
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from types import SimpleNamespace
from uuid import UUID

from helpers import (
    ORG_A_ID, ORG_B_ID, SYSTEM_ADMIN_ROLE_ID, ADMIN_ROLE_ID,
    SYSTEM_ADMIN_USER_ID,
    sys_admin_user, admin_user_a, admin_user_b, admin_user_ab, regular_user_a,
    UpdateUserData,
)

ORG_MODULE = "domains.organizations.services.organization_manager"
USER_MODULE = "domains.users.services.user_manager"


def _fake_org(org_id=ORG_A_ID):
    org = MagicMock()
    org.id = UUID(org_id)
    org.name = "test-org"
    org.slug = "test-org"
    org.is_default = False
    org.description = None
    org.domains = []
    org.settings = {}
    org.created_at = None
    org.updated_at = None
    return org


def _fake_user(user_id="user-1", orgs=None):
    user = MagicMock()
    user.id = user_id
    user.user_name = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.email = "test@test.com"
    user.roles = [ADMIN_ROLE_ID]
    user.organizations = orgs if orgs is not None else [ORG_A_ID]
    user.keycloak_uid = "kc-uid-1"
    user.created_at = None
    user.updated_at = None
    return user


# ═══════════════════════════════════════════════════════════════════
# 1. ADMIN UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

class TestIsSystemAdmin:
    def test_system_admin_role(self):
        from utils.admin import is_system_admin
        assert is_system_admin([SYSTEM_ADMIN_ROLE_ID]) is True

    def test_admin_role_is_not_system_admin(self):
        from utils.admin import is_system_admin
        assert is_system_admin([ADMIN_ROLE_ID]) is False

    def test_empty_roles(self):
        from utils.admin import is_system_admin
        assert is_system_admin([]) is False


class TestCheckOrgScope:
    def test_system_admin_bypasses(self):
        from utils.admin import check_org_scope
        assert check_org_scope(sys_admin_user(), ORG_B_ID) is True

    def test_admin_in_target_org(self):
        from utils.admin import check_org_scope
        assert check_org_scope(admin_user_a(), ORG_A_ID) is True

    def test_admin_not_in_target_org(self):
        from utils.admin import check_org_scope
        assert check_org_scope(admin_user_a(), ORG_B_ID) is False

    def test_multi_org_admin(self):
        from utils.admin import check_org_scope
        assert check_org_scope(admin_user_ab(), ORG_A_ID) is True
        assert check_org_scope(admin_user_ab(), ORG_B_ID) is True

    def test_regular_user_in_org(self):
        from utils.admin import check_org_scope
        assert check_org_scope(regular_user_a(), ORG_A_ID) is True

    def test_regular_user_not_in_org(self):
        from utils.admin import check_org_scope
        assert check_org_scope(regular_user_a(), ORG_B_ID) is False


class TestCheckUserOrgOverlap:
    def test_system_admin_bypasses(self):
        from utils.admin import check_user_org_overlap
        assert check_user_org_overlap(sys_admin_user(), [ORG_B_ID]) is True

    def test_shared_org(self):
        from utils.admin import check_user_org_overlap
        assert check_user_org_overlap(admin_user_a(), [ORG_A_ID, ORG_B_ID]) is True

    def test_no_shared_org(self):
        from utils.admin import check_user_org_overlap
        assert check_user_org_overlap(admin_user_a(), [ORG_B_ID]) is False

    def test_both_empty(self):
        from utils.admin import check_user_org_overlap
        user = {"id": "x", "roles": [ADMIN_ROLE_ID], "organizations": []}
        assert check_user_org_overlap(user, []) is False

    def test_target_user_no_orgs(self):
        from utils.admin import check_user_org_overlap
        assert check_user_org_overlap(admin_user_a(), []) is False


# ═══════════════════════════════════════════════════════════════════
# 2. ORGANIZATION MANAGER PERMISSIONS
# ═══════════════════════════════════════════════════════════════════

class TestOrgManagerPermissions:
    """Verify org manager enforces check_org_scope for scoped operations."""

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_update_org_denied_for_non_member(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_B_ID)
        data = SimpleNamespace(org_id=ORG_B_ID, name=None, description=None, domains=None, settings=None)
        result = await mgr.update_org(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.kc_update_org", new_callable=AsyncMock)
    @patch(f"{ORG_MODULE}.update_organization", new_callable=AsyncMock)
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_update_org_allowed_for_system_admin(self, mock_find, mock_update, mock_kc):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_B_ID)
        data = SimpleNamespace(org_id=ORG_B_ID, name=None, description="updated", domains=None, settings=None)
        result = await mgr.update_org(data, request_user=sys_admin_user())

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_add_user_to_org_denied_for_non_member(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_B_ID)
        data = SimpleNamespace(org_id=ORG_B_ID, user_id="user-1")
        result = await mgr.add_user_to_org(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_remove_user_from_org_denied_for_non_member(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_B_ID)
        data = SimpleNamespace(org_id=ORG_B_ID, user_id="user-1")
        result = await mgr.remove_user_from_org(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_get_members_denied_for_non_member(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_B_ID)
        data = SimpleNamespace(org_id=ORG_B_ID)
        result = await mgr.get_members(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.get_org_users", new_callable=AsyncMock, return_value=[])
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_get_members_allowed_for_member(self, mock_find, mock_users):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_A_ID)
        data = SimpleNamespace(org_id=ORG_A_ID)
        result = await mgr.get_members(data, request_user=admin_user_a())

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_get_org_by_id_denied_for_non_member(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_B_ID)
        data = SimpleNamespace(org_id=ORG_B_ID)
        result = await mgr.get_org(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.find_by_id", new_callable=AsyncMock)
    async def test_get_all_orgs_filtered_for_non_sysadmin(self, mock_find):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_find.return_value = _fake_org(ORG_A_ID)
        data = SimpleNamespace(org_id=None)
        result = await mgr.get_org(data, request_user=admin_user_a())

        assert result["status"] == "success"
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    @patch(f"{ORG_MODULE}.get_all_organizations", new_callable=AsyncMock)
    async def test_get_all_orgs_unfiltered_for_sysadmin(self, mock_all):
        from domains.organizations.services.organization_manager import OrganizationManager
        mgr = OrganizationManager()

        mock_all.return_value = [_fake_org(ORG_A_ID), _fake_org(ORG_B_ID)]
        data = SimpleNamespace(org_id=None)
        result = await mgr.get_org(data, request_user=sys_admin_user())

        assert result["status"] == "success"
        assert len(result["data"]) == 2


# ═══════════════════════════════════════════════════════════════════
# 3. USER MANAGER PERMISSIONS
# ═══════════════════════════════════════════════════════════════════

class TestUserManagerPermissions:
    """Verify user manager enforces org overlap for cross-user operations."""

    @pytest.mark.asyncio
    @patch(f"{USER_MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_get_user_cross_org_denied(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_find.return_value = _fake_user(user_id="target", orgs=[ORG_B_ID])
        data = SimpleNamespace(user_id="target")
        result = await mgr.get_user(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{USER_MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_get_user_cross_org_allowed_for_sysadmin(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_find.return_value = _fake_user(user_id="target", orgs=[ORG_B_ID])
        data = SimpleNamespace(user_id="target")
        result = await mgr.get_user(data, request_user=sys_admin_user())

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{USER_MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_delete_user_cross_org_denied(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_find.return_value = _fake_user(user_id="target", orgs=[ORG_B_ID])
        data = SimpleNamespace(user_id="target")
        result = await mgr.delete_user(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{USER_MODULE}.delete_user", new_callable=AsyncMock, return_value=True)
    @patch(f"{USER_MODULE}.delete_user_from_keycloak", new_callable=AsyncMock, return_value={"status": "success"})
    @patch(f"{USER_MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_delete_user_cross_org_allowed_for_sysadmin(self, mock_find, mock_kc, mock_del):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_find.return_value = _fake_user(user_id="target", orgs=[ORG_B_ID])
        data = SimpleNamespace(user_id="target")
        result = await mgr.delete_user(data, request_user=sys_admin_user())

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{USER_MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_update_user_cross_org_denied(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        with patch(f"{USER_MODULE}.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            mock_find.return_value = _fake_user(user_id="target", orgs=[ORG_B_ID])
            data = SimpleNamespace(
                user_id="target", user_name=None, first_name=None,
                last_name=None, email=None, roles=None,
            )
            result = await mgr.update_user(data, request_user=admin_user_a())

            assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{USER_MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_update_user_same_org_allowed(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        with patch(f"{USER_MODULE}.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            user = _fake_user(user_id="target", orgs=[ORG_A_ID])
            mock_find.return_value = user

            with patch(f"{USER_MODULE}.update_user", new_callable=AsyncMock, return_value=user):
                with patch(f"{USER_MODULE}.update_user_in_keycloak", new_callable=AsyncMock, return_value={"status": "success"}):
                    data = UpdateUserData(user_id="target", first_name="Updated")
                    result = await mgr.update_user(data, request_user=admin_user_a())

                    assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{USER_MODULE}.find_org_by_id", new_callable=AsyncMock)
    @patch(f"{USER_MODULE}.kc_add_member", new_callable=AsyncMock, return_value=True)
    @patch(f"{USER_MODULE}.update_user", new_callable=AsyncMock)
    @patch(f"{USER_MODULE}.create_user", new_callable=AsyncMock)
    @patch(f"{USER_MODULE}.add_user_to_keycloak", new_callable=AsyncMock)
    @patch(f"{USER_MODULE}.get_all_roles", new_callable=AsyncMock)
    @patch(f"{USER_MODULE}.check_email_exists", new_callable=AsyncMock, return_value=False)
    @patch(f"{USER_MODULE}.check_username_exists", new_callable=AsyncMock, return_value=False)
    async def test_create_user_in_foreign_org_denied(
        self, mock_user_ex, mock_email_ex, mock_roles, mock_kc_add,
        mock_db_create, mock_update, mock_kc_member, mock_find_org,
    ):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_roles.return_value = {
            "status": "success",
            "roles": [{"id": ADMIN_ROLE_ID, "name": "admin"}, {"id": "role-user-333", "name": "user"}],
        }
        mock_kc_add.return_value = {"status": "success", "keycloakUserId": "kc-new"}
        mock_db_create.return_value = _fake_user(user_id="new-user", orgs=[])

        data = SimpleNamespace(
            user_name="newuser", first_name="N", last_name="U",
            email="n@u.com", roles=["admin"], enable_mfa=False, org_id=ORG_B_ID,
        )
        result = await mgr.create_user(data, request_user=admin_user_a())

        assert result["status"] == "failed"


# ═══════════════════════════════════════════════════════════════════
# 4. GATEWAY ORG ACCESS CHECK
# ═══════════════════════════════════════════════════════════════════

class TestGatewayOrgAccess:
    """Test the gateway-level check_org_access function."""

    @pytest.mark.asyncio
    async def test_system_admin_bypasses(self):
        with patch("core.config.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            # Import after patching to avoid import-time config issues
            import importlib
            import sys as _sys
            _sys.path.insert(0, "C:\\Users\\shalo\\PycharmProjects\\auth-gateway-fastapi-keycloak\\gateway\\src")
            from services.proxy import check_org_access

            user = {"id": SYSTEM_ADMIN_USER_ID, "organizations": []}
            result = await check_org_access({"org_id": ORG_B_ID}, user)
            assert result is False

    @pytest.mark.asyncio
    async def test_user_in_org_allowed(self):
        with patch("core.config.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            from services.proxy import check_org_access

            user = {"id": "admin-a-id", "organizations": [ORG_A_ID]}
            result = await check_org_access({"org_id": ORG_A_ID}, user)
            assert result is False

    @pytest.mark.asyncio
    async def test_user_not_in_org_denied(self):
        with patch("core.config.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            from services.proxy import check_org_access

            user = {"id": "admin-a-id", "organizations": [ORG_A_ID]}
            result = await check_org_access({"org_id": ORG_B_ID}, user)
            assert result is True

    @pytest.mark.asyncio
    async def test_org_id_from_path(self):
        with patch("core.config.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            from services.proxy import check_org_access

            user = {"id": "admin-a-id", "organizations": [ORG_A_ID]}
            result = await check_org_access({}, user, path=ORG_B_ID)
            assert result is True

    @pytest.mark.asyncio
    async def test_no_org_id_passes(self):
        with patch("core.config.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            from services.proxy import check_org_access

            user = {"id": "admin-a-id", "organizations": [ORG_A_ID]}
            result = await check_org_access({}, user)
            assert result is False

    @pytest.mark.asyncio
    async def test_user_with_no_orgs_denied(self):
        with patch("core.config.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value=SYSTEM_ADMIN_USER_ID)

            from services.proxy import check_org_access

            user = {"id": "regular-no-org", "organizations": []}
            result = await check_org_access({"org_id": ORG_A_ID}, user)
            assert result is True
