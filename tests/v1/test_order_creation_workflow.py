import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.order import Order
from tests.constants import ORG_ID, USER_ID


def test_order_creation_with_items(client, session, current_user, current_org):
    """Test successful order creation with order items"""
    
    mock_order = Order(
        id=uuid4().hex,
        organization_id=ORG_ID,
        customer_id=uuid4().hex,
        order_number="ORD-001",
        status="pending",
        total_amount=150.00,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "customer_id": str(uuid4()),
        "order_items": [
            {
                "product_id": str(uuid4()),
                "quantity": 2,
                "unit_price": 75.00
            }
        ],
        "total_amount": 150.00
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.order.Order.create", return_value=mock_order):
        response = client.post(
            "/api/v1/orders",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["total_amount"] == 150.00


def test_order_status_update(client, session, current_user, current_org):
    """Test updating order status"""
    
    mock_order = Order(
        id=uuid4().hex,
        organization_id=ORG_ID,
        status="processing",
        total_amount=150.00
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.order.Order.update", return_value=mock_order):
        response = client.patch(
            f"/api/v1/orders/{mock_order.id}",
            headers=headers,
            json={"status": "processing"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "processing"
