import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.invoice import Invoice
from tests.constants import ORG_ID, USER_ID


def test_invoice_generation_from_order(client, session, current_user, current_org):
    """Test invoice generation from order"""
    
    mock_invoice = Invoice(
        id=uuid4().hex,
        organization_id=ORG_ID,
        order_id=uuid4().hex,
        invoice_number="INV-001",
        status="draft",
        total_amount=150.00,
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "order_id": str(uuid4()),
        "due_date": "2024-12-31",
        "notes": "Payment due within 30 days"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.invoice.Invoice.create", return_value=mock_invoice):
        response = client.post(
            "/api/v1/invoices",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["invoice_number"] == "INV-001"


def test_invoice_status_update(client, session, current_user, current_org):
    """Test updating invoice status to paid"""
    
    mock_invoice = Invoice(
        id=uuid4().hex,
        organization_id=ORG_ID,
        status="paid",
        total_amount=150.00
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.invoice.Invoice.update", return_value=mock_invoice):
        response = client.patch(
            f"/api/v1/invoices/{mock_invoice.id}",
            headers=headers,
            json={"status": "paid"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "paid"
