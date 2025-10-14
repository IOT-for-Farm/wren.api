import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.template import Template
from tests.constants import ORG_ID, USER_ID


def test_template_creation_success(client, session, current_user, current_org):
    """Test successful template creation"""
    
    mock_template = Template(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="Email Welcome Template",
        type="email",
        content="Welcome to our platform!",
        variables=["user_name", "company_name"],
        is_active=True,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Email Welcome Template",
        "type": "email",
        "content": "Welcome to our platform!",
        "variables": ["user_name", "company_name"]
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.template.Template.create", return_value=mock_template):
        response = client.post(
            "/api/v1/templates",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Email Welcome Template"


def test_template_activation(client, session, current_user, current_org):
    """Test template activation/deactivation"""
    
    mock_template = Template(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="Email Welcome Template",
        is_active=False
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.template.Template.update", return_value=mock_template):
        response = client.patch(
            f"/api/v1/templates/{mock_template.id}",
            headers=headers,
            json={"is_active": False},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["is_active"] is False
