import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.organization import Organization
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_organization():
    return Organization(
        id=ORG_ID,
        name="Test Organization",
        slug="test-organization",
        description="A test organization",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_organization(client, session, current_user):
    """Test creating a new organization successfully"""
    
    app.dependency_overrides[Organization.create] = lambda: mock_organization

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_organization()

    payload = {
        "name": "New Organization",
        "description": "A new test organization",
        "website": "https://testorg.com"
    }

    with patch("api.v1.models.organization.Organization.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/organizations", 
            headers=headers,
            json=payload
        )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
