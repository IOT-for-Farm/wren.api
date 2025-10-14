import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.review import Review
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_review():
    return Review(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Review"),
        organization_id=ORG_ID,
        model_type="product",
        model_id=uuid4().hex,
        reviewer_id=USER_ID,
        rating=5,
        title="Great Product",
        comment="This product exceeded my expectations",
        is_verified=True,
        is_public=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_review(client, session, current_user, current_org):
    """Test creating a new review successfully"""
    
    app.dependency_overrides[Review.create] = lambda: mock_review

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_review()

    payload = {
        "model_type": "product",
        "model_id": uuid4().hex,
        "rating": 4,
        "title": "Good Product",
        "comment": "This product meets my needs well",
        "is_verified": False,
        "is_public": True
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.review.Review.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/reviews", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["title"] == payload["title"]
