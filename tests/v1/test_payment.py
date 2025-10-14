import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.payment import Payment
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_payment():
    return Payment(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Payment"),
        organization_id=ORG_ID,
        payment_reference="PAY-001",
        amount=250.00,
        payment_method="credit_card",
        status="completed",
        payment_date=datetime.now(timezone.utc),
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_payment(client, session, current_user, current_org):
    """Test creating a new payment successfully"""
    
    app.dependency_overrides[Payment.create] = lambda: mock_payment

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_payment()

    payload = {
        "payment_reference": "PAY-002",
        "amount": 300.00,
        "payment_method": "bank_transfer",
        "status": "pending",
        "payment_date": "2024-01-20T14:30:00Z"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.payment.Payment.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/payments", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["payment_reference"] == payload["payment_reference"]
