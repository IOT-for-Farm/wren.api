import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.department import Department
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_department():
    return Department(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Department"),
        organization_id=ORG_ID,
        name="Test Department",
        description="A test department for organization",
        code="DEPT001",
        is_active=True,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_department(client, session, current_user, current_org):
    """Test creating a new department successfully"""
    
    app.dependency_overrides[Department.create] = lambda: mock_department

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_department()

    payload = {
        "name": "Engineering",
        "description": "Software engineering department",
        "code": "ENG001",
        "is_active": True
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.department.Department.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/departments", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
