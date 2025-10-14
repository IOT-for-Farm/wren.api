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


def test_user_registration_success(client, session):
    """Test successful user registration with valid data"""
    
    mock_user = User(
        id=USER_ID,
        email="newuser@gmail.com",
        password=AuthService.hash_secret("Testpassword@123"),
        first_name="New",
        last_name="User",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "email": "newuser@gmail.com",
        "password": "Testpassword@123",
        "first_name": "New",
        "last_name": "User"
    }
    
    with patch("api.v1.models.user.User.create", return_value=mock_user):
        response = client.post("/api/v1/auth/signup", json=payload)
        
        assert response.status_code == 201
        assert response.json()["data"]["email"] == payload["email"]
        assert response.json()["data"]["first_name"] == payload["first_name"]


def test_user_registration_duplicate_email(client, session):
    """Test registration failure with duplicate email"""
    
    # Mock existing user
    existing_user = User(
        id=USER_ID,
        email="existing@gmail.com",
        password=AuthService.hash_secret("Testpassword@123"),
        first_name="Existing",
        last_name="User",
        is_active=True
    )
    
    session.query.return_value.filter.return_value.first.return_value = existing_user
    
    payload = {
        "email": "existing@gmail.com",
        "password": "Testpassword@123",
        "first_name": "New",
        "last_name": "User"
    }
    
    response = client.post("/api/v1/auth/signup", json=payload)
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_user_registration_weak_password(client, session):
    """Test registration failure with weak password"""
    
    payload = {
        "email": "newuser@gmail.com",
        "password": "123",  # Weak password
        "first_name": "New",
        "last_name": "User"
    }
    
    response = client.post("/api/v1/auth/signup", json=payload)
    
    assert response.status_code == 422
    # Should contain validation error for password strength


def test_user_registration_missing_fields(client, session):
    """Test registration failure with missing required fields"""
    
    payload = {
        "email": "newuser@gmail.com",
        "password": "Testpassword@123"
        # Missing first_name and last_name
    }
    
    response = client.post("/api/v1/auth/signup", json=payload)
    
    assert response.status_code == 422
    # Should contain validation errors for missing fields


def test_user_registration_invalid_email_format(client, session):
    """Test registration failure with invalid email format"""
    
    payload = {
        "email": "invalid-email-format",
        "password": "Testpassword@123",
        "first_name": "New",
        "last_name": "User"
    }
    
    response = client.post("/api/v1/auth/signup", json=payload)
    
    assert response.status_code == 422
    # Should contain validation error for email format
