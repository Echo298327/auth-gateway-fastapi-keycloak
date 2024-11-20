import pytest
from unittest.mock import patch, MagicMock
from users.src.manager import create_user, update_user, delete_user, get_user


@pytest.mark.asyncio
@patch("users.src.manager.User")
@patch("users.src.manager.generate_password")
@patch("users.src.manager.send_password_email")
@patch("users.src.manager.add_user_to_keycloak")
async def test_create_user(mock_add_user_to_keycloak, mock_send_password_email, mock_generate_password, mock_user):
    # Arrange mocks
    mock_generate_password.return_value = "test_password"
    mock_add_user_to_keycloak.return_value = {"status": "success", "keycloakUserId": "test_id"}

    # Mocking the database lookup for an existing user (no existing user found)
    mock_user.objects.return_value.first.side_effect = [
        None,  # No existing user with the given username
        mock_user  # Returning user instance after saving
    ]

    # Mocking user creation
    mock_user.return_value.save.return_value = None
    mock_user.return_value.id = "test_id"

    data = MagicMock()
    data.dict.return_value = {
        "user_name": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "role_id": "test_role",
        "email": "testuser@example.com"
    }

    response = await create_user(data)

    assert response["status"] == "success"
    assert "user_id" in response
    mock_user.return_value.save.assert_called_once()
    mock_send_password_email.assert_not_called()  # since it's commented out in the function


@pytest.mark.asyncio
@patch("users.src.manager.User")
@patch("users.src.manager.update_user_in_keycloak")
async def test_update_user_success(mock_update_user_in_keycloak, mock_user):
    user_id = "test_id"

    # Mock the data input
    data = MagicMock()
    data.dict.return_value = {
        "user_id": user_id,
        "user_name": "new_username",
        "first_name": "New",
        "last_name": "User",
        "role_id": "new_role",
        "email": "newuser@example.com"
    }

    # Mocking the database lookup for an existing user
    mock_user_instance = MagicMock()
    mock_user.objects.return_value.first.side_effect = [
        mock_user_instance,  # User found for updating
        None  # No user found with the new username to avoid conflict
    ]

    mock_user.objects.return_value.update.return_value = None
    mock_update_user_in_keycloak.return_value = {"status": "success"}

    response = await update_user(data)

    assert response["status"] == "success"
    assert response["message"] == "User updated successfully"
    mock_user.objects.return_value.update.assert_called_once()  # Ensure update is called


@pytest.mark.asyncio
@patch("users.src.manager.User")
@patch("users.src.manager.delete_user_from_keycloak")
async def test_delete_user(mock_delete_user_from_keycloak, mock_user):
    mock_user.objects.return_value.first.return_value = MagicMock(id="test_id")
    mock_delete_user_from_keycloak.return_value = {"status": "success"}

    data = MagicMock()
    data.dict.return_value = {
        "user_id": "test_id"
    }

    response = await delete_user(data)

    assert response["status"] == "success"
    assert response["message"] == "User deleted successfully"
    mock_user.objects.return_value.first.return_value.delete.assert_called_once()


@pytest.mark.asyncio
@patch("users.src.manager.User")
async def test_get_user(mock_user):
    mock_user.objects.return_value.first.return_value = MagicMock(
        id="test_id",
        user_name="test_user",
        first_name="Test",
        last_name="User",
        role_id="test_role",
        email="testuser@example.com",
        keycloak_uid="keycloak_uid",
        creation_date="2024-11-15 10:00:00"
    )

    data = MagicMock()
    data.dict.return_value = {
        "user_id": "test_id"
    }

    response = await get_user(data)

    assert response["status"] == "success"
    assert response["data"]["user_name"] == "test_user"
    assert response["data"]["first_name"] == "Test"
    assert response["data"]["last_name"] == "User"
    mock_user.objects.return_value.first.assert_called_once()
