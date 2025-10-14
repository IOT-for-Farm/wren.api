import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.content import Content
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_content():
    return Content(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Content"),
        organization_id=ORG_ID,
        title="Test Content",
        body="This is a test content body",
        author_id=USER_ID,
        content_type="article",
        visibility="public",
        content_status="published",
        review_status="approved",
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_content(client, session, current_user, current_org):
    """Test creating a new content successfully"""
    
    app.dependency_overrides[Content.create] = lambda: mock_content

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_content()

    payload = {
        "title": "How to Use Our API",
        "body": "This article explains how to integrate with our API endpoints...",
        "content_type": "article",
        "visibility": "public",
        "content_status": "draft",
        "seo_title": "API Integration Guide",
        "seo_description": "Learn how to integrate with our REST API"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.content.Content.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/contents", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["title"] == payload["title"]
