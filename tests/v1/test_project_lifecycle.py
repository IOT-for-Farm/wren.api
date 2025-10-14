import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.project import Project
from tests.constants import ORG_ID, USER_ID


def test_project_creation_success(client, session, current_user, current_org):
    """Test successful project creation"""
    
    mock_project = Project(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="Website Redesign",
        description="Complete website overhaul",
        status="planning",
        start_date=datetime.now(timezone.utc),
        budget=50000.00,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Website Redesign",
        "description": "Complete website overhaul",
        "budget": 50000.00,
        "start_date": "2024-01-15T00:00:00Z"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.project.Project.create", return_value=mock_project):
        response = client.post(
            "/api/v1/projects",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Website Redesign"


def test_project_status_progression(client, session, current_user, current_org):
    """Test project status progression from planning to active"""
    
    mock_project = Project(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="Website Redesign",
        status="active"
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.project.Project.update", return_value=mock_project):
        response = client.patch(
            f"/api/v1/projects/{mock_project.id}",
            headers=headers,
            json={"status": "active"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "active"
