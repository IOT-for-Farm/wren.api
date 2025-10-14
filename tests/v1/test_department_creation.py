import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.department import Department
from tests.constants import ORG_ID, USER_ID


def test_department_creation_success(client, session, current_user, current_org):
    """Test successful department creation"""
    
    mock_department = Department(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="Engineering",
        description="Software development team",
        budget=100000.00,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Engineering",
        "description": "Software development team",
        "budget": 100000.00
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.department.Department.create", return_value=mock_department):
        response = client.post(
            "/api/v1/departments",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Engineering"


def test_department_budget_update(client, session, current_user, current_org):
    """Test department budget update"""
    
    mock_department = Department(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="Engineering",
        budget=150000.00
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.department.Department.update", return_value=mock_department):
        response = client.patch(
            f"/api/v1/departments/{mock_department.id}",
            headers=headers,
            json={"budget": 150000.00},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["budget"] == 150000.00
