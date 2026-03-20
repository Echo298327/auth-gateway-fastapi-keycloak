import sys
import os
from unittest.mock import MagicMock, patch

import pytest

# Pre-mock auth_gateway_serverkit and all sub-modules before anything imports them
_mocked_modules = [
    "auth_gateway_serverkit",
    "auth_gateway_serverkit.logger",
    "auth_gateway_serverkit.password",
    "auth_gateway_serverkit.string",
    "auth_gateway_serverkit.http_client",
    "auth_gateway_serverkit.request_handler",
    "auth_gateway_serverkit.keycloak",
    "auth_gateway_serverkit.keycloak.user",
    "auth_gateway_serverkit.keycloak.role",
    "auth_gateway_serverkit.keycloak.organization",
    "auth_gateway_serverkit.keycloak.client",
    "auth_gateway_serverkit.keycloak.config",
    "auth_gateway_serverkit.keycloak.initializer",
    "auth_gateway_serverkit.keycloak.realm",
    "auth_gateway_serverkit.middleware",
    "auth_gateway_serverkit.middleware.auth",
    "auth_gateway_serverkit.middleware.schemas",
    "auth_gateway_serverkit.middleware.config",
]

for mod_name in _mocked_modules:
    mock_mod = MagicMock()
    mock_mod.__name__ = mod_name
    mock_mod.__path__ = []
    mock_mod.__file__ = None
    mock_mod.__loader__ = None
    mock_mod.__spec__ = None
    mock_mod.__package__ = mod_name
    sys.modules[mod_name] = mock_mod

# Wire parent → child relationships so attribute access works
sys.modules["auth_gateway_serverkit"].logger = sys.modules["auth_gateway_serverkit.logger"]
sys.modules["auth_gateway_serverkit"].password = sys.modules["auth_gateway_serverkit.password"]
sys.modules["auth_gateway_serverkit"].string = sys.modules["auth_gateway_serverkit.string"]
sys.modules["auth_gateway_serverkit"].http_client = sys.modules["auth_gateway_serverkit.http_client"]
sys.modules["auth_gateway_serverkit"].request_handler = sys.modules["auth_gateway_serverkit.request_handler"]
sys.modules["auth_gateway_serverkit"].keycloak = sys.modules["auth_gateway_serverkit.keycloak"]
sys.modules["auth_gateway_serverkit"].middleware = sys.modules["auth_gateway_serverkit.middleware"]
sys.modules["auth_gateway_serverkit.keycloak"].user = sys.modules["auth_gateway_serverkit.keycloak.user"]
sys.modules["auth_gateway_serverkit.keycloak"].role = sys.modules["auth_gateway_serverkit.keycloak.role"]
sys.modules["auth_gateway_serverkit.keycloak"].organization = sys.modules["auth_gateway_serverkit.keycloak.organization"]
sys.modules["auth_gateway_serverkit.keycloak"].client = sys.modules["auth_gateway_serverkit.keycloak.client"]
sys.modules["auth_gateway_serverkit.keycloak"].config = sys.modules["auth_gateway_serverkit.keycloak.config"]
sys.modules["auth_gateway_serverkit.keycloak"].initializer = sys.modules["auth_gateway_serverkit.keycloak.initializer"]
sys.modules["auth_gateway_serverkit.keycloak"].realm = sys.modules["auth_gateway_serverkit.keycloak.realm"]
sys.modules["auth_gateway_serverkit.middleware"].auth = sys.modules["auth_gateway_serverkit.middleware.auth"]
sys.modules["auth_gateway_serverkit.middleware"].schemas = sys.modules["auth_gateway_serverkit.middleware.schemas"]
sys.modules["auth_gateway_serverkit.middleware"].config = sys.modules["auth_gateway_serverkit.middleware.config"]

# Make init_logger return a standard mock logger everywhere
sys.modules["auth_gateway_serverkit.logger"].init_logger = MagicMock(return_value=MagicMock())

# Make string validators pass by default
sys.modules["auth_gateway_serverkit.string"].is_valid_user_name = MagicMock(return_value=True)
sys.modules["auth_gateway_serverkit.string"].is_valid_name = MagicMock(return_value=True)

_iam_src = os.path.join(os.path.dirname(__file__), "..", "src")
_gateway_src = os.path.join(os.path.dirname(__file__), "..", "..", "gateway", "src")

sys.path.insert(0, os.path.abspath(_iam_src))
sys.path.insert(0, os.path.abspath(_gateway_src))
sys.path.insert(0, os.path.dirname(__file__))

# Pre-mock core.config to prevent Settings() instantiation (requires env vars not
# available in CI). Must happen before any module imports core.config.
_config_mock = MagicMock()
_config_mock.__name__ = "core.config"
_config_mock.__path__ = []
_config_mock.__file__ = None
_config_mock.__loader__ = None
_config_mock.__spec__ = None
_config_mock.__package__ = "core.config"
sys.modules["core.config"] = _config_mock

from helpers import SYSTEM_ADMIN_ROLE_ID, ADMIN_ROLE_ID


@pytest.fixture(autouse=True)
def _patch_settings():
    """Patch IAM settings so admin util functions work without a real DB."""
    with patch("utils.admin.settings") as mock_settings:
        mock_settings.has_system_admin_role_id.return_value = True
        mock_settings.has_admin_role_id.return_value = True
        mock_settings.SYSTEM_ADMIN_ROLE_ID = SYSTEM_ADMIN_ROLE_ID
        mock_settings.ADMIN_ROLE_ID = ADMIN_ROLE_ID
        yield mock_settings
