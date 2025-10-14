import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.content import Content
from tests.constants import ORG_ID, USER_ID


def test_content_creation_success(client, session, current_user, current_org):
    """Test successful content creation"""
    
    mock_content = Content(
        id=uuid4().hex,
        organization_id=ORG_ID,
        title="Blog Post Title",
        content="This is the blog post content...",
        type="blog",
        status="published",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "title": "Blog Post Title",
        "content": "This is the blog post content...",
        "type": "blog",
        "status": "published"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.content.Content.create", return_value=mock_content):
        response = client.post(
            "/api/v1/content",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["title"] == "Blog Post Title"


def test_content_status_update(client, session, current_user, current_org):
    """Test content status update to draft"""
    
    mock_content = Content(
        id=uuid4().hex,
        organization_id=ORG_ID,
        title="Blog Post Title",
        status="draft"
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.content.Content.update", return_value=mock_content):
        response = client.patch(
            f"/api/v1/content/{mock_content.id}",
            headers=headers,
            json={"status": "draft"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "draft"
