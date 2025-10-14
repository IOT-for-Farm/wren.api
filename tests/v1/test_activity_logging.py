import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.activity_log import ActivityLog
from tests.constants import ORG_ID, USER_ID


def test_activity_log_creation_success(client, session, current_user, current_org):
    """Test successful activity log creation"""
    
    mock_activity = ActivityLog(
        id=uuid4().hex,
        organization_id=ORG_ID,
        user_id=USER_ID,
        action="created",
        resource_type="product",
        resource_id=uuid4().hex,
        description="Product created successfully",
        metadata={"product_name": "Test Product"},
        created_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "action": "created",
        "resource_type": "product",
        "resource_id": str(uuid4()),
        "description": "Product created successfully",
        "metadata": {"product_name": "Test Product"}
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.activity_log.ActivityLog.create", return_value=mock_activity):
        response = client.post(
            "/api/v1/activity-logs",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["action"] == "created"


def test_activity_log_retrieval(client, session, current_user, current_org):
    """Test activity log retrieval by user"""
    
    mock_activities = [
        ActivityLog(
            id=uuid4().hex,
            organization_id=ORG_ID,
            user_id=USER_ID,
            action="created",
            resource_type="product"
        )
    ]
    
    params = {"organization_id": current_org.id, "user_id": USER_ID}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.activity_log.ActivityLog.fetch_by_user", return_value=mock_activities):
        response = client.get(
            "/api/v1/activity-logs",
            headers=headers,
            params=params
        )
        
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
        assert response.json()["data"][0]["action"] == "created"
