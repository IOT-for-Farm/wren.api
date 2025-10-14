import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.comment import Comment
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_comment():
    return Comment(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Comment"),
        organization_id=ORG_ID,
        model_type="content",
        model_id=uuid4().hex,
        author_id=USER_ID,
        content="This is a test comment",
        is_approved=True,
        is_public=True,
        parent_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_comment(client, session, current_user, current_org):
    """Test creating a new comment successfully"""
    
    app.dependency_overrides[Comment.create] = lambda: mock_comment

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_comment()

    payload = {
        "model_type": "content",
        "model_id": uuid4().hex,
        "content": "Great article! Very informative.",
        "is_approved": True,
        "is_public": True,
        "parent_id": None
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.comment.Comment.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/comments", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["content"] == payload["content"]
