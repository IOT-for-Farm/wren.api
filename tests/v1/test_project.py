import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.project import Project
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_project():
    return Project(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Project"),
        organization_id=ORG_ID,
        name="Test Project",
        description="A test project for development",
        status="active",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
        budget=50000.00,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_project(client, session, current_user, current_org):
    """Test creating a new project successfully"""
    
    app.dependency_overrides[Project.create] = lambda: mock_project

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_project()

    payload = {
        "name": "Website Redesign",
        "description": "Complete redesign of company website",
        "status": "planning",
        "budget": 25000.00,
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-06-30T23:59:59Z"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.project.Project.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/projects", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
