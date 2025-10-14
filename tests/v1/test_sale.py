import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.sale import Sale
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_sale():
    return Sale(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Sale"),
        organization_id=ORG_ID,
        sale_number="SALE-001",
        customer_id=uuid4().hex,
        total_amount=800.00,
        discount_amount=50.00,
        status="completed",
        sale_date=datetime.now(timezone.utc),
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_sale(client, session, current_user, current_org):
    """Test creating a new sale successfully"""
    
    app.dependency_overrides[Sale.create] = lambda: mock_sale

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_sale()

    payload = {
        "sale_number": "SALE-002",
        "customer_id": uuid4().hex,
        "total_amount": 1200.00,
        "discount_amount": 100.00,
        "status": "processing",
        "sale_date": "2024-01-25T16:45:00Z"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.sale.Sale.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/sales", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["sale_number"] == payload["sale_number"]
