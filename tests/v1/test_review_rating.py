import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.review import Review
from tests.constants import ORG_ID, USER_ID


def test_review_creation_success(client, session, current_user, current_org):
    """Test successful review creation"""
    
    mock_review = Review(
        id=uuid4().hex,
        organization_id=ORG_ID,
        model_type="product",
        model_id=uuid4().hex,
        reviewer_id=USER_ID,
        rating=5,
        title="Excellent Product",
        comment="Highly recommended!",
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "model_type": "product",
        "model_id": str(uuid4()),
        "rating": 5,
        "title": "Excellent Product",
        "comment": "Highly recommended!"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.review.Review.create", return_value=mock_review):
        response = client.post(
            "/api/v1/reviews",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["rating"] == 5


def test_review_moderation(client, session, current_user, current_org):
    """Test review moderation approval"""
    
    mock_review = Review(
        id=uuid4().hex,
        organization_id=ORG_ID,
        rating=4,
        is_verified=True,
        is_public=True
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.review.Review.update", return_value=mock_review):
        response = client.patch(
            f"/api/v1/reviews/{mock_review.id}",
            headers=headers,
            json={"is_verified": True, "is_public": True},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["is_verified"] is True
