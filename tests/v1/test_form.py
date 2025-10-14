import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.form import Form
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_form():
    return Form(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Form"),
        organization_id=ORG_ID,
        form_template_id=uuid4().hex,
        title="Test Form",
        description="A test form for data collection",
        form_data={"fields": [{"name": "email", "type": "email"}]},
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_form(client, session, current_user, current_org):
    """Test creating a new form successfully"""
    
    app.dependency_overrides[Form.create] = lambda: mock_form

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_form()

    payload = {
        "form_template_id": uuid4().hex,
        "title": "Contact Form",
        "description": "A contact form for customer inquiries",
        "form_data": {
            "fields": [
                {"name": "name", "type": "text", "required": True},
                {"name": "email", "type": "email", "required": True},
                {"name": "message", "type": "textarea", "required": True}
            ]
        }
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.form.Form.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/forms", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["title"] == payload["title"]
