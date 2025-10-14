import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.category import Category
from tests.constants import ORG_ID, USER_ID


def test_category_creation_success(client, session, current_user, current_org):
    """Test successful category creation"""
    
    mock_category = Category(
        id=uuid4().hex,
        name="Electronics",
        description="Electronic products",
        slug="electronics",
        model_type="product",
        organization_id=ORG_ID,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Electronics",
        "description": "Electronic products",
        "model_type": "product"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.category.Category.create", return_value=mock_category):
        response = client.post(
            "/api/v1/categories",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Electronics"


def test_category_retrieval_by_id(client, session, current_user, current_org):
    """Test retrieving category by ID"""
    
    mock_category = Category(
        id=uuid4().hex,
        name="Electronics",
        description="Electronic products",
        organization_id=ORG_ID
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.category.Category.fetch_by_id", return_value=mock_category):
        response = client.get(
            f"/api/v1/categories/{mock_category.id}",
            headers=headers,
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Electronics"
