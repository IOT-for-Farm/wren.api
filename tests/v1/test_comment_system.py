import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.comment import Comment
from tests.constants import ORG_ID, USER_ID


def test_comment_creation_success(client, session, current_user, current_org):
    """Test successful comment creation"""
    
    mock_comment = Comment(
        id=uuid4().hex,
        organization_id=ORG_ID,
        model_type="product",
        model_id=uuid4().hex,
        author_id=USER_ID,
        content="This is a great product!",
        is_approved=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "model_type": "product",
        "model_id": str(uuid4()),
        "content": "This is a great product!"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.comment.Comment.create", return_value=mock_comment):
        response = client.post(
            "/api/v1/comments",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["content"] == "This is a great product!"


def test_comment_moderation(client, session, current_user, current_org):
    """Test comment moderation approval"""
    
    mock_comment = Comment(
        id=uuid4().hex,
        organization_id=ORG_ID,
        content="This is a great product!",
        is_approved=True
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.comment.Comment.update", return_value=mock_comment):
        response = client.patch(
            f"/api/v1/comments/{mock_comment.id}",
            headers=headers,
            json={"is_approved": True},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["is_approved"] is True
