import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.activity_log import ActivityLog
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_activity_log():
    return ActivityLog(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Activity Log"),
        organization_id=ORG_ID,
        user_id=USER_ID,
        action="create",
        model_type="product",
        model_id=uuid4().hex,
        description="Product created successfully",
        metadata={"product_name": "Test Product"},
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_activity_log(client, session, current_user, current_org):
    """Test creating a new activity log successfully"""
    
    app.dependency_overrides[ActivityLog.create] = lambda: mock_activity_log

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_activity_log()

    payload = {
        "user_id": USER_ID,
        "action": "update",
        "model_type": "customer",
        "model_id": uuid4().hex,
        "description": "Customer information updated",
        "metadata": {"field": "email", "old_value": "old@email.com", "new_value": "new@email.com"},
        "ip_address": "192.168.1.100",
        "user_agent": "Chrome/91.0"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.activity_log.ActivityLog.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/activity-logs", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["action"] == payload["action"]
