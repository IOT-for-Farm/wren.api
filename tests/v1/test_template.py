import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.template import Template
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_template():
    return Template(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Template"),
        organization_id=ORG_ID,
        name="Test Template",
        description="A test template for content creation",
        template_type="email",
        content="<html><body>{{content}}</body></html>",
        variables=["content", "title"],
        is_active=True,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_template(client, session, current_user, current_org):
    """Test creating a new template successfully"""
    
    app.dependency_overrides[Template.create] = lambda: mock_template

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_template()

    payload = {
        "name": "Welcome Email Template",
        "description": "Template for welcome emails",
        "template_type": "email",
        "content": "<html><body><h1>Welcome {{name}}!</h1><p>{{message}}</p></body></html>",
        "variables": ["name", "message"],
        "is_active": True
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.template.Template.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/templates", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
