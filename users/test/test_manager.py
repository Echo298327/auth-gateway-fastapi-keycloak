import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from mongoengine import connect, disconnect
import mongomock
import time
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import after path is set
from users.src.manager import UserManager, User


# Test Data Class
class MockData:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def dict(self):
        return {k: v for k, v in self.__dict__.items()}


@pytest.fixture(autouse=True)
def mongo_connection():
    """Setup MongoDB mock connection for testing"""
    disconnect()  # Disconnect from any existing connections
    connect('mongoenginetest', mongo_client_class=mongomock.MongoClient)
    yield
    disconnect()


@pytest.fixture
def user_manager():
    """Create UserManager instance for testing"""
    return UserManager()


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.start_transaction = MagicMock()
    session.commit_transaction = MagicMock()
    session.abort_transaction = MagicMock()
    session.end_session = MagicMock()
    return session


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
class TestUserManager:
    
    async def test_create_system_admin_success(self, user_manager):
        """Test successful system admin creation"""
        with patch('users.src.manager.add_user_to_keycloak') as mock_keycloak, \
             patch('users.src.manager.settings') as mock_settings:
            mock_keycloak.return_value = {
                'status': 'success',
                'keycloakUserId': 'test-keycloak-id'
            }
            mock_settings.SYSTEM_ADMIN_USER_NAME = 'system_admin'
            mock_settings.SYSTEM_ADMIN_FIRST_NAME = 'System'
            mock_settings.SYSTEM_ADMIN_LAST_NAME = 'Admin'
            mock_settings.SYSTEM_ADMIN_EMAIL = 'admin@system.com'
            mock_settings.SYSTEM_ADMIN_PASSWORD = 'password123'
            
            result = await user_manager.create_system_admin()
            
            assert result is True
            created_user = User.objects(user_name='system_admin').first()
            assert created_user is not None
            assert created_user.roles == ['systemAdmin']

    async def test_create_system_admin_already_exists(self, user_manager):
        """Test system admin creation when admin already exists"""
        # Create the system admin first
        User(
            user_name='system_admin',
            first_name='System',
            last_name='Admin',
            roles=['systemAdmin'],
            email='admin@system.com',
            keycloak_uid='existing-id',
            creation_date=time.strftime("%d-%m-%Y")
        ).save()

        # Mock Keycloak and settings
        with patch('users.src.manager.add_user_to_keycloak') as mock_keycloak, \
             patch('users.src.manager.settings') as mock_settings:
            # Setup mock values
            mock_settings.SYSTEM_ADMIN_USER_NAME = 'system_admin'
            mock_settings.SYSTEM_ADMIN_FIRST_NAME = 'System'
            mock_settings.SYSTEM_ADMIN_LAST_NAME = 'Admin'
            mock_settings.SYSTEM_ADMIN_EMAIL = 'admin@system.com'
            mock_settings.SYSTEM_ADMIN_PASSWORD = 'password123'
            
            result = await user_manager.create_system_admin()
            assert result is True

    async def test_create_user_success(self, user_manager, mock_db_session):
        """Test successful user creation"""
        with patch('users.src.manager.get_db') as mock_get_db, \
             patch('users.src.manager.add_user_to_keycloak') as mock_keycloak, \
             patch('users.src.manager.is_valid_names') as mock_validate:
            
            mock_get_db.return_value.client.start_session.return_value = mock_db_session
            mock_keycloak.return_value = {'status': 'success', 'keycloakUserId': 'test-id'}
            mock_validate.return_value = (True, [])
            
            data = MockData(
                user_name='testuser',
                first_name='Test',
                last_name='User',
                email='test@example.com',
                roles=['user']
            )
            
            result = await user_manager.create_user(data)
            
            assert result['status'] == 'success'
            assert 'user_id' in result
            created_user = User.objects(user_name='testuser').first()
            assert created_user is not None

    async def test_create_user_invalid_names(self, user_manager, mock_db_session):
        """Test user creation with invalid names"""
        with patch('users.src.manager.get_db') as mock_get_db, \
             patch('users.src.manager.is_valid_names') as mock_validate:
            
            mock_get_db.return_value.client.start_session.return_value = mock_db_session
            mock_validate.return_value = (False, ['Invalid username'])
            
            data = MockData(
                user_name='invalid user',
                first_name='Test',
                last_name='User',
                email='test@example.com',
                roles=['user']
            )
            
            result = await user_manager.create_user(data)
            
            assert result['status'] == 'failed'
            assert 'Invalid username' in result['message']

    async def test_update_user_success(self, user_manager, mock_db_session):
        """Test successful user update"""
        user = User(
            user_name='oldname',
            first_name='Old',
            last_name='Name',
            email='old@test.com',
            roles=['user'],
            keycloak_uid='test-id',
            creation_date=time.strftime("%d-%m-%Y")
        ).save()

        with patch('users.src.manager.get_db') as mock_get_db, \
             patch('users.src.manager.update_user_in_keycloak') as mock_keycloak, \
             patch('users.src.manager.is_valid_names') as mock_validate:
            
            mock_get_db.return_value.client.start_session.return_value = mock_db_session
            mock_keycloak.return_value = {'status': 'success'}
            mock_validate.return_value = (True, [])
            
            data = MockData(
                user_id=str(user.id),
                user_name='newname',
                first_name='New',
                last_name='Name',
                email='new@test.com',
                roles=['user']
            )
            
            result = await user_manager.update_user(data, user_roles=['admin'])
            
            assert result['status'] == 'success'
            updated_user = User.objects(id=user.id).first()
            assert updated_user.user_name == 'newname'
            assert updated_user.email == 'new@test.com'

    async def test_delete_user_success(self, user_manager):
        """Test successful user deletion"""
        user = User(
            user_name='deleteuser',
            first_name='Delete',
            last_name='User',
            email='delete@test.com',
            roles=['user'],
            keycloak_uid='delete-id',
            creation_date=time.strftime("%d-%m-%Y")
        ).save()

        with patch('users.src.manager.delete_user_from_keycloak') as mock_keycloak:
            mock_keycloak.return_value = {'status': 'success'}
            
            data = MockData(user_id=str(user.id))
            result = await user_manager.delete_user(data)
            
            assert result['status'] == 'success'
            assert User.objects(id=user.id).first() is None

    async def test_delete_user_not_found(self, user_manager):
        """Test deletion of non-existent user"""
        data = MockData(user_id=str(ObjectId()))
        result = await user_manager.delete_user(data)
        
        assert result['status'] == 'failed'
        assert result['message'] == 'User not found'

    async def test_get_user_success(self, user_manager):
        """Test successful user retrieval"""
        user = User(
            user_name='getuser',
            first_name='Get',
            last_name='User',
            email='get@test.com',
            roles=['user'],
            keycloak_uid='get-id',
            creation_date=time.strftime("%d-%m-%Y")
        ).save()

        data = MockData(user_id=str(user.id))
        result = await user_manager.get_user(data)
        
        assert result['status'] == 'success'
        assert result['data']['user_name'] == 'getuser'
        assert result['data']['email'] == 'get@test.com'

    async def test_get_user_by_keycloak_uid_success(self, user_manager):
        """Test successful user retrieval by Keycloak UID"""
        user = User(
            user_name='keycloakuser',
            first_name='Keycloak',
            last_name='User',
            email='keycloak@test.com',
            roles=['user'],
            keycloak_uid='specific-keycloak-id',
            creation_date=time.strftime("%d-%m-%Y")
        ).save()

        data = MockData(keycloak_uid='specific-keycloak-id')
        result = await user_manager.get_user_by_keycloak_uid(data)
        
        assert result['status'] == 'success'
        assert result['data']['user_name'] == 'keycloakuser'
        assert result['data']['keycloak_uid'] == 'specific-keycloak-id'

    async def test_create_user_keycloak_failure(self, user_manager, mock_db_session):
        """Test user creation when Keycloak fails"""
        with patch('users.src.manager.get_db') as mock_get_db, \
             patch('users.src.manager.add_user_to_keycloak') as mock_keycloak, \
             patch('users.src.manager.is_valid_names') as mock_validate:
            
            mock_get_db.return_value.client.start_session.return_value = mock_db_session
            mock_keycloak.return_value = {'status': 'failed', 'message': 'Keycloak error'}
            mock_validate.return_value = (True, [])
            
            data = MockData(
                user_name='testuser',
                first_name='Test',
                last_name='User',
                email='test@example.com',
                roles=['user']
            )
            
            result = await user_manager.create_user(data)
            
            assert result['status'] == 'failed'
            assert 'Error creating user in Keycloak' in result['message']

    async def test_update_user_unauthorized_roles(self, user_manager, mock_db_session):
        """Test updating user roles without proper authorization"""
        user = User(
            user_name='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            roles=['user'],
            keycloak_uid='test-id',
            creation_date=time.strftime("%d-%m-%Y")
        ).save()

        with patch('users.src.manager.get_db') as mock_get_db, \
             patch('users.src.manager.is_valid_names') as mock_validate:
            
            mock_get_db.return_value.client.start_session.return_value = mock_db_session
            mock_validate.return_value = (True, [])
            
            data = MockData(
                user_id=str(user.id),
                user_name='testuser',  # Add required fields
                first_name='Test',
                last_name='User',
                email='test@example.com',
                roles=['admin']  # Attempting to update to admin role
            )
            
            result = await user_manager.update_user(data, user_roles=['user'])
            
            assert result['status'] == 'failed'
            assert 'Unauthorized to update roles' in result['message']

    async def test_delete_user_keycloak_failure(self, user_manager):
        """Test user deletion when Keycloak deletion fails"""
        user = User(
            user_name='deleteuser',
            first_name='Delete',
            last_name='User',
            email='delete@test.com',
            roles=['user'],
            keycloak_uid='delete-id',
            creation_date=time.strftime("%d-%m-%Y")
        ).save()

        with patch('users.src.manager.delete_user_from_keycloak') as mock_keycloak:
            mock_keycloak.return_value = {'status': 'failed', 'message': 'Keycloak error'}
            
            data = MockData(user_id=str(user.id))
            result = await user_manager.delete_user(data)
            
            assert result['status'] == 'fail'
            assert 'Keycloak error' in result['message']
            # Verify user still exists in database
            assert User.objects(id=user.id).first() is not None

    async def test_update_user_not_found(self, user_manager, mock_db_session):
        """Test updating non-existent user"""
        with patch('users.src.manager.get_db') as mock_get_db:
            mock_get_db.return_value.client.start_session.return_value = mock_db_session
            
            data = MockData(
                user_id=str(ObjectId()),
                user_name='newname',
                email='new@test.com',
                roles=[]
            )
            
            result = await user_manager.update_user(data)
            
            assert result['status'] == 'failed'
            assert 'User not found' in result['message']
