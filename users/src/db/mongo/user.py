"""
Database operations for users collection.
This module provides an abstraction layer for user database operations,
decoupling the service layer from MongoDB-specific implementations.
"""

from models.user import User
from typing import Optional, Union, List
from bson import ObjectId
from datetime import datetime


async def find_by_user_id(user_id: Union[ObjectId, str]) -> Optional[User]:
    """
    Find a user by user ID.

    Args:
        user_id: User ID to search for

    Returns:
        User object if found, None otherwise
    """
    return await User.find_one({"_id": ObjectId(user_id) if isinstance(user_id, str) else user_id})


async def find_by_username(username: str) -> Optional[User]:
    """
    Find a user by username.

    Args:
        username: Username to search for (will be converted to lowercase)

    Returns:
        User object if found, None otherwise
    """
    return await User.find_one({"user_name": username.lower()})


async def find_by_email(email: str) -> Optional[User]:
    """
    Find a user by email.

    Args:
        email: Email to search for

    Returns:
        User object if found, None otherwise
    """
    return await User.find_one({"email": email})


async def find_by_keycloak_uid(keycloak_uid: str) -> Optional[User]:
    """
    Find a user by Keycloak UID.

    Args:
        keycloak_uid: Keycloak UID to search for

    Returns:
        User object if found, None otherwise
    """
    return await User.find_one({"keycloak_uid": keycloak_uid})


async def create_user(
    user_name: str,
    first_name: str,
    last_name: str,
    roles: List[str],
    email: str,
    keycloak_uid: str
) -> User:
    """
    Create a new user document.

    Args:
        user_name: Username (will be converted to lowercase)
        first_name: First name
        last_name: Last name
        roles: List[str]
        email: Email address
        keycloak_uid: Keycloak user ID

    Returns:
        Created User object
    """
    user = User(
        user_name=user_name.lower(),
        first_name=first_name,
        last_name=last_name,
        roles=roles,
        email=email,
        keycloak_uid=keycloak_uid,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return await user.insert()


async def update_user(user: User, **kwargs) -> User:
    """
    Update an existing user document.

    Args:
        user: User object to update
        **kwargs: Fields to update

    Returns:
        Updated User object
    """
    # Handle username conversion to lowercase
    if 'user_name' in kwargs:
        kwargs['user_name'] = kwargs['user_name'].lower()
    
    # Update fields
    for field, value in kwargs.items():
        if value is not None and hasattr(user, field):
            setattr(user, field, value)
    
    # Update timestamp
    user.updated_at = datetime.utcnow()
    
    await user.save()
    return user


async def delete_user(user_id: Union[ObjectId, str]) -> bool:
    """
    Delete a user by user ID.

    Args:
        user_id: User ID to delete

    Returns:
        True if user was deleted, False if user not found
    """
    user = await find_by_user_id(user_id)
    if not user:
        return False
    
    await user.delete()
    return True


async def check_username_exists(username: str, exclude_user_id: Optional[Union[ObjectId, str]] = None) -> bool:
    """
    Check if a username already exists (excluding a specific user ID).

    Args:
        username: Username to check
        exclude_user_id: User ID to exclude from the check (for updates)

    Returns:
        True if username exists, False otherwise
    """
    query = {"user_name": username.lower()}
    
    if exclude_user_id:
        exclude_id = ObjectId(exclude_user_id) if isinstance(exclude_user_id, str) else exclude_user_id
        query["_id"] = {"$ne": exclude_id}
    
    user = await User.find_one(query)
    return user is not None


async def check_email_exists(email: str, exclude_user_id: Optional[Union[ObjectId, str]] = None) -> bool:
    """
    Check if an email already exists (excluding a specific user ID).

    Args:
        email: Email to check
        exclude_user_id: User ID to exclude from the check (for updates)

    Returns:
        True if email exists, False otherwise
    """
    query = {"email": email}
    
    if exclude_user_id:
        exclude_id = ObjectId(exclude_user_id) if isinstance(exclude_user_id, str) else exclude_user_id
        query["_id"] = {"$ne": exclude_id}
    
    user = await User.find_one(query)
    return user is not None


async def get_all_users(limit: Optional[int] = None, skip: Optional[int] = None) -> List[User]:
    """
    Get all users with optional pagination.

    Args:
        limit: Maximum number of users to return
        skip: Number of users to skip

    Returns:
        List of User objects
    """
    query = User.find()
    
    if skip:
        query = query.skip(skip)
    
    if limit:
        query = query.limit(limit)
    
    return await query.to_list()


async def get_users_by_roles(role_ids: List[str]) -> List[User]:
    """
    Get users that have any of the specified roles.

    Args:
        role_ids: List of role IDs to search for

    Returns:
        List of User objects
    """
    return await User.find({"roles": {"$in": role_ids}}).to_list()


async def count_users() -> int:
    """
    Get the total count of users.

    Returns:
        Number of users in the collection
    """
    return await User.count()


async def user_exists(user_id: Union[ObjectId, str]) -> bool:
    """
    Check if a user exists by user ID.

    Args:
        user_id: User ID to check

    Returns:
        True if user exists, False otherwise
    """
    user = await find_by_user_id(user_id)
    return user is not None
