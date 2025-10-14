import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.product import Product
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def test_product_creation_with_all_fields(client, session, current_user, current_org):
    """Test successful product creation with all required fields"""
    
    mock_product = Product(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Product"),
        organization_id=ORG_ID,
        name="Test Product",
        slug="test-product",
        description="A comprehensive test product",
        price=99.99,
        cost=50.00,
        sku="TEST-SKU-001",
        status="published",
        type="physical",
        is_available=True,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Test Product",
        "description": "A comprehensive test product",
        "price": 99.99,
        "cost": 50.00,
        "sku": "TEST-SKU-001",
        "status": "published",
        "type": "physical",
        "is_available": True
    }
    
    params = {"organization_id": current_org.id}
    
    with patch("api.v1.models.product.Product.create", return_value=mock_product):
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/products",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]
        assert response.json()["data"]["price"] == payload["price"]
        assert response.json()["data"]["status"] == payload["status"]


def test_product_creation_minimal_fields(client, session, current_user, current_org):
    """Test successful product creation with minimal required fields"""
    
    mock_product = Product(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Minimal Product"),
        organization_id=ORG_ID,
        name="Minimal Product",
        slug="minimal-product",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Minimal Product"
    }
    
    params = {"organization_id": current_org.id}
    
    with patch("api.v1.models.product.Product.create", return_value=mock_product):
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/products",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == payload["name"]


def test_product_creation_digital_type(client, session, current_user, current_org):
    """Test successful creation of digital product type"""
    
    mock_product = Product(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Digital Product"),
        organization_id=ORG_ID,
        name="Digital Product",
        slug="digital-product",
        description="A digital download product",
        price=29.99,
        status="published",
        type="digital",
        is_available=True,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "Digital Product",
        "description": "A digital download product",
        "price": 29.99,
        "type": "digital",
        "status": "published"
    }
    
    params = {"organization_id": current_org.id}
    
    with patch("api.v1.models.product.Product.create", return_value=mock_product):
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/products",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["type"] == "digital"
        assert response.json()["data"]["price"] == 29.99
