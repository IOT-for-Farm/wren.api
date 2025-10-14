import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.invoice import Invoice
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_invoice():
    return Invoice(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Invoice"),
        organization_id=ORG_ID,
        invoice_number="INV-001",
        customer_id=uuid4().hex,
        total_amount=1000.00,
        tax_amount=100.00,
        status="draft",
        due_date=datetime.now(timezone.utc),
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_invoice(client, session, current_user, current_org):
    """Test creating a new invoice successfully"""
    
    app.dependency_overrides[Invoice.create] = lambda: mock_invoice

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_invoice()

    payload = {
        "invoice_number": "INV-002",
        "customer_id": uuid4().hex,
        "total_amount": 1500.00,
        "tax_amount": 150.00,
        "status": "pending",
        "due_date": "2024-12-31T23:59:59Z"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.invoice.Invoice.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/invoices", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["invoice_number"] == payload["invoice_number"]
