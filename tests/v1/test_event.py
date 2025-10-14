import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.event import Event
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_event():
    return Event(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Event"),
        organization_id=ORG_ID,
        title="Test Event",
        description="A test event for organization",
        event_type="meeting",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
        location="Conference Room A",
        status="scheduled",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_event(client, session, current_user, current_org):
    """Test creating a new event successfully"""
    
    app.dependency_overrides[Event.create] = lambda: mock_event

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_event()

    payload = {
        "title": "Team Meeting",
        "description": "Weekly team standup meeting",
        "event_type": "meeting",
        "start_date": "2024-02-01T09:00:00Z",
        "end_date": "2024-02-01T10:00:00Z",
        "location": "Virtual Meeting",
        "status": "scheduled"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.event.Event.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/events", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["title"] == payload["title"]
