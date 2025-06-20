import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# EARLY MOCK: Mock the auth_gateway_serverkit modules before they get imported
# This prevents the config validation errors in GitHub Actions
class EarlyMockSettings:
    def __init__(self, *args, **kwargs):
        # Don't actually validate anything - just create a mock settings object
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Set required attributes
        self.SERVER_URL = "http://127.0.0.1:9000"
        self.CLIENT_ID = "templateApp"
        self.REALM = "templateRealm"
        self.SCOPE = "openid"
        self.KC_BOOTSTRAP_ADMIN_USERNAME = "admin"
        self.KC_BOOTSTRAP_ADMIN_PASSWORD = "admin"

early_mock_config = MagicMock()
early_mock_config.settings = EarlyMockSettings()
early_mock_config.Settings = EarlyMockSettings
sys.modules['config'] = early_mock_config
sys.modules['auth_gateway_serverkit.keycloak.config'] = early_mock_config

# Create a mock Settings class
class MockSettings:
    def __init__(self):
        self.SERVER_URL = "http://127.0.0.1:9000"
        self.CLIENT_ID = "templateApp"
        self.REALM = "templateRealm"
        self.SCOPE = "openid"
        self.KEYCLOAK_FRONTEND_URL = "http://keycloak:9000"
        self.KC_BOOTSTRAP_ADMIN_USERNAME = "admin"
        self.KC_BOOTSTRAP_ADMIN_PASSWORD = "admin"
        self.AUTHORIZATION_URL = f"{self.SERVER_URL}/auth/realms/{self.REALM}/protocol/openid-connect/auth"
        self.TOKEN_URL = f"{self.SERVER_URL}/auth/realms/{self.REALM}/protocol/openid-connect/token"
        
        # App settings
        self.MONGO_CONNECTION_STRING = "mongodb://localhost:27017"
        self.DB_NAME = "templateApp"
        self.PORT = 8081
        self.HOST = "localhost"
        self.APP_EMAIL = "admin@example.com"
        self.APP_PASSWORD = "xxx xxx xxx"
        
        # System admin settings
        self.SYSTEM_ADMIN_USER_NAME = "sysadmin"
        self.SYSTEM_ADMIN_FIRST_NAME = "None"
        self.SYSTEM_ADMIN_LAST_NAME = "None"
        self.SYSTEM_ADMIN_EMAIL = "sysadmin@dev.com"
        self.SYSTEM_ADMIN_PASSWORD = "sysadminpassword"

# Create mock module
mock_config = MagicMock()
mock_config.settings = MockSettings()
mock_config.Settings = MockSettings

# Patch the config import that auth_gateway_serverkit uses
sys.modules['config'] = mock_config

# Create a special mock for auth_gateway_serverkit.keycloak.config that prevents Settings() from being called
def mock_settings_init(*args, **kwargs):
    return MockSettings()

mock_keycloak_config = MagicMock()
mock_keycloak_config.settings = MockSettings()
mock_keycloak_config.Settings = mock_settings_init
sys.modules['auth_gateway_serverkit.keycloak.config'] = mock_keycloak_config

# Create mock objects for any additional settings that might be needed
local_settings = MagicMock()
local_settings.SYSTEM_ADMIN_USER_NAME = "system_admin"
local_settings.SYSTEM_ADMIN_FIRST_NAME = "System"
local_settings.SYSTEM_ADMIN_LAST_NAME = "Admin"
local_settings.SYSTEM_ADMIN_EMAIL = "admin@system.com"
local_settings.SYSTEM_ADMIN_PASSWORD = "admin123"
local_settings.MONGODB_URL = "mongodb://localhost:27017/testdb"
local_settings.DATABASE_NAME = "testdb"

# Patch only the local settings
patch('users.src.config.settings', local_settings).start()

@pytest.fixture(autouse=True)
def cleanup_patches():
    """Clean up patches after tests"""
    yield
    patch.stopall()