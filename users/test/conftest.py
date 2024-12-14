import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Set environment variables for testing
os.environ.update({
    # Keycloak settings
    'SERVER_URL': 'http://127.0.0.1:9000',
    'CLIENT_ID': 'templateApp',
    'REALM': 'templateRealm',
    'SCOPE': 'openid',
    'KEYCLOAK_FRONTEND_URL': 'http://keycloak:9000',
    'KC_BOOTSTRAP_ADMIN_USERNAME': 'admin',
    'KC_BOOTSTRAP_ADMIN_PASSWORD': 'admin',
    'AUTHORIZATION_URL': 'http://127.0.0.1:9000/auth/realms/templateRealm/protocol/openid-connect/auth',
    'TOKEN_URL': 'http://127.0.0.1:9000/auth/realms/templateRealm/protocol/openid-connect/token',

    # App settings
    'USERS_PORT': '8081',
    'USERS_HOST': 'localhost',
    'MONGO_CONNECTION_STRING': 'mongodb://localhost:27017',
    'DB_NAME': 'templateApp',
    'APP_EMAIL': 'admin@example.com',
    'APP_PASSWORD': 'xxx xxx xxx',

    # System admin settings
    'SYSTEM_ADMIN_USER_NAME': 'sysadmin',
    'SYSTEM_ADMIN_FIRST_NAME': 'None',
    'SYSTEM_ADMIN_LAST_NAME': 'None',
    'SYSTEM_ADMIN_EMAIL': 'sysadmin@dev.com',
    'SYSTEM_ADMIN_PASSWORD': 'sysadminpassword'
})

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