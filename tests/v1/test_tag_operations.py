import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.tag import Tag
from tests.constants import ORG_ID, USER_ID


def test_tag_creation_success(client, session, current_user, current_org):
    """Test successful tag creation"""
    
    mock_tag = Tag(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="urgent",
        color="#FF0000",
        description="High priority items",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "urgent",
        "color": "#FF0000",
        "description": "High priority items"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.tag.Tag.create", return_value=mock_tag):
        response = client.post(
            "/api/v1/tags",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "urgent"


def test_tag_assignment_to_entity(client, session, current_user, current_org):
    """Test tag assignment to entity"""
    
    tag_id = uuid4().hex
    entity_id = uuid4().hex
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.tag.Tag.assign_to_entity", return_value={"success": True}):
        response = client.post(
            f"/api/v1/tags/{tag_id}/assign",
            headers=headers,
            json={"entity_type": "product", "entity_id": entity_id},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
