"""
User flow tests — positive and negative scenarios for
create, update, delete, and get.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from types import SimpleNamespace

from helpers import (
    ORG_A_ID, ADMIN_ROLE_ID, SYSTEM_ADMIN_ROLE_ID,
    admin_user_a, sys_admin_user, regular_user_a,
    UpdateUserData,
)

MODULE = "domains.users.services.user_manager"


def _fake_db_user(user_id="user-1", user_name="testuser", orgs=None, keycloak_uid="kc-1"):
    user = MagicMock()
    user.id = user_id
    user.user_name = user_name
    user.first_name = "Test"
    user.last_name = "User"
    user.email = "test@example.com"
    user.roles = [ADMIN_ROLE_ID]
    user.organizations = orgs if orgs is not None else [ORG_A_ID]
    user.keycloak_uid = keycloak_uid
    user.created_at = None
    user.updated_at = None
    return user


def _realm_roles():
    return {
        "status": "success",
        "roles": [
            {"id": ADMIN_ROLE_ID, "name": "admin"},
            {"id": "role-user-333", "name": "user"},
            {"id": SYSTEM_ADMIN_ROLE_ID, "name": "systemAdmin"},
        ]
    }


# ── CREATE ──────────────────────────────────────────────────────────

class TestCreateUser:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.kc_add_member", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.find_default_org", new_callable=AsyncMock)
    @patch(f"{MODULE}.update_user", new_callable=AsyncMock)
    @patch(f"{MODULE}.create_user", new_callable=AsyncMock)
    @patch(f"{MODULE}.add_user_to_keycloak", new_callable=AsyncMock)
    @patch(f"{MODULE}.get_all_roles", new_callable=AsyncMock)
    @patch(f"{MODULE}.check_email_exists", new_callable=AsyncMock, return_value=False)
    @patch(f"{MODULE}.check_username_exists", new_callable=AsyncMock, return_value=False)
    async def test_create_success(self, mock_user_exists, mock_email_exists,
                                  mock_roles, mock_kc_add, mock_db_create,
                                  mock_update, mock_default_org, mock_kc_member):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_roles.return_value = _realm_roles()
        mock_kc_add.return_value = {"status": "success", "keycloakUserId": "kc-new"}
        fake_user = _fake_db_user(user_id="new-user-id", orgs=[])
        mock_db_create.return_value = fake_user

        fake_org = MagicMock()
        fake_org.id = ORG_A_ID
        mock_default_org.return_value = fake_org

        data = SimpleNamespace(
            user_name="newuser", first_name="New", last_name="User",
            email="new@test.com", roles=["admin"], enable_mfa=False, org_id=None,
        )
        result = await mgr.create_user(data, request_user=sys_admin_user())

        assert result["status"] == "success"
        assert "user_id" in result

    @pytest.mark.asyncio
    @patch(f"{MODULE}.check_username_exists", new_callable=AsyncMock, return_value=True)
    async def test_create_duplicate_username(self, mock_exists):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        data = SimpleNamespace(
            user_name="existing", first_name="A", last_name="B",
            email="a@b.com", roles=["admin"], enable_mfa=False, org_id=None,
        )
        result = await mgr.create_user(data)

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.check_email_exists", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.check_username_exists", new_callable=AsyncMock, return_value=False)
    async def test_create_duplicate_email(self, mock_user, mock_email):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        data = SimpleNamespace(
            user_name="unique", first_name="A", last_name="B",
            email="dup@test.com", roles=["admin"], enable_mfa=False, org_id=None,
        )
        result = await mgr.create_user(data)

        assert result["status"] == "failed"


# ── UPDATE ──────────────────────────────────────────────────────────

class TestUpdateUser:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.settings")
    @patch(f"{MODULE}.update_user_in_keycloak", new_callable=AsyncMock, return_value={"status": "success"})
    @patch(f"{MODULE}.update_user", new_callable=AsyncMock)
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_self_update_success(self, mock_find, mock_update, mock_kc, mock_settings):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_settings.get_system_admin_id = AsyncMock(return_value="sys-admin-id-000")
        user = _fake_db_user(user_id="admin-a-id")
        mock_find.return_value = user
        mock_update.return_value = user

        data = UpdateUserData(first_name="Updated")
        result = await mgr.update_user(data, request_user=admin_user_a())

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.settings")
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_update_not_found(self, mock_find, mock_settings):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_settings.get_system_admin_id = AsyncMock(return_value="sys-admin-id-000")
        mock_find.return_value = None
        data = UpdateUserData(user_id="nonexistent")
        result = await mgr.update_user(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_update_system_admin_blocked(self):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        with patch(f"{MODULE}.settings") as mock_settings:
            mock_settings.get_system_admin_id = AsyncMock(return_value="sys-admin-id-000")
            data = UpdateUserData(user_id="sys-admin-id-000")
            result = await mgr.update_user(data, request_user=admin_user_a())

            assert result["status"] == "failed"


# ── DELETE ──────────────────────────────────────────────────────────

class TestDeleteUser:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.delete_user", new_callable=AsyncMock, return_value=True)
    @patch(f"{MODULE}.delete_user_from_keycloak", new_callable=AsyncMock, return_value={"status": "success"})
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_delete_success(self, mock_find, mock_kc, mock_del):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_find.return_value = _fake_db_user()
        data = SimpleNamespace(user_id="user-1")
        result = await mgr.delete_user(data, request_user=admin_user_a())

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock, return_value=None)
    async def test_delete_not_found(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        data = SimpleNamespace(user_id="nonexistent")
        result = await mgr.delete_user(data, request_user=admin_user_a())

        assert result["status"] == "failed"


# ── GET ─────────────────────────────────────────────────────────────

class TestGetUser:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_get_self_success(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_find.return_value = _fake_db_user(user_id="admin-a-id")
        data = SimpleNamespace(user_id=None)
        result = await mgr.get_user(data, request_user=admin_user_a())

        assert result["status"] == "success"
        assert result["data"]["id"] == "admin-a-id"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock)
    async def test_get_other_user_same_org(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        mock_find.return_value = _fake_db_user(user_id="user-1", orgs=[ORG_A_ID])
        data = SimpleNamespace(user_id="user-1")
        result = await mgr.get_user(data, request_user=admin_user_a())

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.find_by_user_id", new_callable=AsyncMock, return_value=None)
    async def test_get_not_found(self, mock_find):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        data = SimpleNamespace(user_id="nonexistent")
        result = await mgr.get_user(data, request_user=admin_user_a())

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_get_other_user_no_admin_role(self):
        from domains.users.services.user_manager import UserManager
        mgr = UserManager()

        data = SimpleNamespace(user_id="someone-else")
        result = await mgr.get_user(data, request_user=regular_user_a())

        assert result["status"] == "failed"
