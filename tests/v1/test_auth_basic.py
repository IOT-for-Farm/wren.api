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


def test_user_login_success(client, session):
    """Test successful user login with valid credentials"""
    
    # Mock user data
    mock_user = User(
        id=USER_ID,
        email="testuser@gmail.com",
        password=AuthService.hash_secret("Testpassword@123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Mock database response
    session.query.return_value.filter.return_value.first.return_value = mock_user
    
    payload = {
        "email": "testuser@gmail.com",
        "password": "Testpassword@123"
    }
    
    with patch("api.v1.services.auth.AuthService.authenticate_user", return_value=mock_user):
        response = client.post("/api/v1/auth/login", json=payload)
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "data" in response.json()
        assert response.json()["data"]["email"] == payload["email"]


def test_user_login_invalid_credentials(client, session):
    """Test login failure with invalid credentials"""
    
    # Mock database response - no user found
    session.query.return_value.filter.return_value.first.return_value = None
    
    payload = {
        "email": "nonexistent@gmail.com",
        "password": "wrongpassword"
    }
    
    with patch("api.v1.services.auth.AuthService.authenticate_user", return_value=None):
        response = client.post("/api/v1/auth/login", json=payload)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


def test_user_login_inactive_account(client, session):
    """Test login failure with inactive account"""
    
    # Mock inactive user
    mock_user = User(
        id=USER_ID,
        email="testuser@gmail.com",
        password=AuthService.hash_secret("Testpassword@123"),
        first_name="Test",
        last_name="User",
        is_active=False,  # Inactive account
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.query.return_value.filter.return_value.first.return_value = mock_user
    
    payload = {
        "email": "testuser@gmail.com",
        "password": "Testpassword@123"
    }
    
    with patch("api.v1.services.auth.AuthService.authenticate_user", return_value=None):
        response = client.post("/api/v1/auth/login", json=payload)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
