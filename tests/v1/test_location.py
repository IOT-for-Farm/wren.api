import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.location import Location
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_location():
    return Location(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Location"),
        organization_id=ORG_ID,
        model_type="organization",
        model_id=ORG_ID,
        name="Test Location",
        address="123 Test Street",
        city="Test City",
        state="Test State",
        country="Test Country",
        postal_code="12345",
        latitude=40.7128,
        longitude=-74.0060,
        is_primary=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_location(client, session, current_user, current_org):
    """Test creating a new location successfully"""
    
    app.dependency_overrides[Location.create] = lambda: mock_location

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_location()

    payload = {
        "model_type": "organization",
        "model_id": current_org.id,
        "name": "Main Office",
        "address": "456 Business Ave",
        "city": "Business City",
        "state": "Business State",
        "country": "Business Country",
        "postal_code": "54321",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "is_primary": False
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.location.Location.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/locations", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
