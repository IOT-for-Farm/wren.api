import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException

from api.utils import helpers
from main import app
from api.v1.models.user import User
from api.v1.services.auth import AuthService
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_user():
    return User(
        id=USER_ID,
        email="testuser@gmail.com",
        password=AuthService.hash_secret("Testpassword@123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_user(client, session, current_org):
    """Test creating a new user successfully"""
    
    app.dependency_overrides[User.create] = lambda: mock_user

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_user()

    payload = {
        "email": "newuser@gmail.com",
        "password": "Testpassword@123",
        "first_name": "New",
        "last_name": "User"
    }

    with patch("api.v1.models.user.User.create", return_value=mock_data) as mock_create:
        response = client.post(
            "/api/v1/auth/signup", 
            json=payload
        )

        assert response.status_code == 201
        assert response.json()["data"]["email"] == payload["email"]
