import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.sale import Sale
from tests.constants import ORG_ID, USER_ID


def test_sale_creation_success(client, session, current_user, current_org):
    """Test successful sale creation"""
    
    mock_sale = Sale(
        id=uuid4().hex,
        organization_id=ORG_ID,
        customer_id=uuid4().hex,
        total_amount=299.99,
        discount_amount=50.00,
        tax_amount=25.00,
        status="completed",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "customer_id": str(uuid4()),
        "total_amount": 299.99,
        "discount_amount": 50.00,
        "tax_amount": 25.00,
        "items": [
            {"product_id": str(uuid4()), "quantity": 2, "unit_price": 149.99}
        ]
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.sale.Sale.create", return_value=mock_sale):
        response = client.post(
            "/api/v1/sales",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["total_amount"] == 299.99


def test_sale_refund_processing(client, session, current_user, current_org):
    """Test sale refund processing"""
    
    mock_sale = Sale(
        id=uuid4().hex,
        organization_id=ORG_ID,
        total_amount=299.99,
        status="refunded",
        refund_amount=299.99
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.sale.Sale.process_refund", return_value=mock_sale):
        response = client.post(
            f"/api/v1/sales/{mock_sale.id}/refund",
            headers=headers,
            json={"refund_amount": 299.99},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "refunded"
