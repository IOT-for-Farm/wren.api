import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from main import app
from api.v1.models.product import Product
from tests.constants import ORG_ID, USER_ID


def test_product_creation_missing_name(client, session, current_user, current_org):
    """Test product creation failure with missing name field"""
    
    payload = {
        "description": "Product without name",
        "price": 99.99
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    response = client.post(
        "/api/v1/products",
        headers=headers,
        json=payload,
        params=params
    )
    
    assert response.status_code == 422


def test_product_creation_negative_price(client, session, current_user, current_org):
    """Test product creation failure with negative price"""
    
    payload = {
        "name": "Test Product",
        "price": -10.00  # Negative price should fail
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    response = client.post(
        "/api/v1/products",
        headers=headers,
        json=payload,
        params=params
    )
    
    assert response.status_code == 422


def test_product_creation_invalid_status(client, session, current_user, current_org):
    """Test product creation failure with invalid status"""
    
    payload = {
        "name": "Test Product",
        "status": "invalid_status"  # Invalid status
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    response = client.post(
        "/api/v1/products",
        headers=headers,
        json=payload,
        params=params
    )
    
    assert response.status_code == 422
