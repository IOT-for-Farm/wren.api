import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.organization import Organization
from tests.constants import ORG_ID, USER_ID


def test_organization_creation_success(client, session, current_user):
    """Test successful organization creation"""
    
    mock_org = Organization(
        id=uuid4().hex,
        name="Test Organization",
        slug="test-org",
        email="test@org.com",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Test Organization",
        "email": "test@org.com",
        "phone_number": "1234567890",
        "phone_country_code": "+1"
    }
    
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.organization.Organization.create", return_value=mock_org):
        response = client.post(
            "/api/v1/organizations",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Test Organization"


def test_organization_update_settings(client, session, current_user, current_org):
    """Test organization settings update"""
    
    mock_org = Organization(
        id=current_org.id,
        name="Updated Organization",
        slug="updated-org",
        email="updated@org.com"
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.organization.Organization.update", return_value=mock_org):
        response = client.patch(
            f"/api/v1/organizations/{current_org.id}",
            headers=headers,
            json={"name": "Updated Organization"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Organization"
