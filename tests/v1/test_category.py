import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.category import Category
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_category():
    return Category(
        id=uuid4().hex,
        name="Test Category",
        description="A test category",
        slug="test-category",
        model_type="product",
        organization_id=ORG_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_category(client, session, current_user, current_org):
    """Test creating a new category successfully"""
    
    app.dependency_overrides[Category.create] = lambda: mock_category

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_category()

    payload = {
        "name": "Electronics",
        "description": "Electronic products category",
        "model_type": "product"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.category.Category.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/categories", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
