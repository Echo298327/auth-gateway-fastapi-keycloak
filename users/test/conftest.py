import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Set environment variables for Keycloak settings
os.environ.update({
    'SERVER_URL': 'http://test-keycloak:8080',
    'CLIENT_ID': 'test-client',
    'REALM': 'test-realm',
    'SCOPE': 'test-scope',
    'KEYCLOAK_FRONTEND_URL': 'http://test-keycloak:8080',
    'KC_BOOTSTRAP_ADMIN_USERNAME': 'admin',
    'KC_BOOTSTRAP_ADMIN_PASSWORD': 'admin',
    # Local settings
    'SYSTEM_ADMIN_USER_NAME': 'system_admin',
    'SYSTEM_ADMIN_FIRST_NAME': 'System',
    'SYSTEM_ADMIN_LAST_NAME': 'Admin',
    'SYSTEM_ADMIN_EMAIL': 'admin@system.com',
    'SYSTEM_ADMIN_PASSWORD': 'admin123',
    'MONGODB_URL': 'mongodb://localhost:27017/testdb',
    'DATABASE_NAME': 'testdb'
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