import pytest
from unittest.mock import patch, MagicMock
from users.src.manager import create_user, update_user, delete_user, get_user


@pytest.mark.asyncio
@patch("users.src.manager.User")
@patch("users.src.manager.generate_password")
@patch("users.src.manager.send_password_email")
async def test_create_user(mock_send_password_email, mock_generate_password, mock_user):
    mock_generate_password.return_value = "test_password"
    mock_user.objects.return_value.first.side_effect = [None, MagicMock(id="test_id")]
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
async def test_update_user(mock_user):
    mock_user.objects.return_value.first.side_effect = [MagicMock(id="test_id"), None]
    mock_user.objects.return_value.update.return_value = None

    data = MagicMock()
    data.dict.return_value = {
        "user_id": "test_id",
        "user_name": "updated_user",
        "first_name": None,
        "last_name": "Updated",
        "role_id": None,
        "email": None
    }

    response = await update_user(data)

    assert response["status"] == "success"
    assert response["message"] == "User updated successfully"


@pytest.mark.asyncio
@patch("users.src.manager.User")
async def test_delete_user(mock_user):
    mock_user.objects.return_value.first.return_value = MagicMock(id="test_id")

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
