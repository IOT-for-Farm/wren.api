import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.form import Form
from tests.constants import ORG_ID, USER_ID


def test_form_creation_success(client, session, current_user, current_org):
    """Test successful form creation"""
    
    mock_form = Form(
        id=uuid4().hex,
        organization_id=ORG_ID,
        title="Customer Feedback Form",
        description="Collect customer feedback",
        fields=[
            {"name": "rating", "type": "number", "required": True},
            {"name": "comments", "type": "text", "required": False}
        ],
        status="active",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "title": "Customer Feedback Form",
        "description": "Collect customer feedback",
        "fields": [
            {"name": "rating", "type": "number", "required": True},
            {"name": "comments", "type": "text", "required": False}
        ]
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.form.Form.create", return_value=mock_form):
        response = client.post(
            "/api/v1/forms",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["title"] == "Customer Feedback Form"


def test_form_submission_success(client, session, current_user, current_org):
    """Test successful form submission"""
    
    form_id = uuid4().hex
    
    payload = {
        "form_id": form_id,
        "submission_data": {
            "rating": 5,
            "comments": "Great service!"
        }
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.form.Form.submit_response", return_value={"id": uuid4().hex}):
        response = client.post(
            "/api/v1/forms/submit",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
