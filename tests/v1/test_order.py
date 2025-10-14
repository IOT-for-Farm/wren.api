import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.order import Order
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_order():
    return Order(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Order"),
        organization_id=ORG_ID,
        order_number="ORD-001",
        customer_id=uuid4().hex,
        total_amount=500.00,
        status="pending",
        order_date=datetime.now(timezone.utc),
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_order(client, session, current_user, current_org):
    """Test creating a new order successfully"""
    
    app.dependency_overrides[Order.create] = lambda: mock_order

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_order()

    payload = {
        "order_number": "ORD-002",
        "customer_id": uuid4().hex,
        "total_amount": 750.00,
        "status": "processing",
        "order_date": "2024-01-15T10:30:00Z"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.order.Order.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/orders", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["order_number"] == payload["order_number"]
