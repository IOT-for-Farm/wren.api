import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.event import Event
from tests.constants import ORG_ID, USER_ID


def test_event_creation_success(client, session, current_user, current_org):
    """Test successful event creation"""
    
    mock_event = Event(
        id=uuid4().hex,
        organization_id=ORG_ID,
        title="Team Meeting",
        description="Weekly team standup",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
        location="Conference Room A",
        status="scheduled",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "title": "Team Meeting",
        "description": "Weekly team standup",
        "location": "Conference Room A",
        "start_date": "2024-01-15T10:00:00Z",
        "end_date": "2024-01-15T11:00:00Z"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.event.Event.create", return_value=mock_event):
        response = client.post(
            "/api/v1/events",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["title"] == "Team Meeting"


def test_event_status_update(client, session, current_user, current_org):
    """Test event status update to completed"""
    
    mock_event = Event(
        id=uuid4().hex,
        organization_id=ORG_ID,
        title="Team Meeting",
        status="completed"
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.event.Event.update", return_value=mock_event):
        response = client.patch(
            f"/api/v1/events/{mock_event.id}",
            headers=headers,
            json={"status": "completed"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "completed"
