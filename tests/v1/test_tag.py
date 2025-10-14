import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.tag import Tag
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_tag():
    return Tag(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Tag"),
        organization_id=ORG_ID,
        name="Test Tag",
        description="A test tag for categorization",
        color="#FF5733",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_tag(client, session, current_user, current_org):
    """Test creating a new tag successfully"""
    
    app.dependency_overrides[Tag.create] = lambda: mock_tag

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_tag()

    payload = {
        "name": "Important",
        "description": "Tag for important items",
        "color": "#FF0000",
        "is_active": True
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.tag.Tag.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/tags", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
