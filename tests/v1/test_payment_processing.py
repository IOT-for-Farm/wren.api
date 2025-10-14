import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.payment import Payment
from tests.constants import ORG_ID, USER_ID


def test_payment_creation_success(client, session, current_user, current_org):
    """Test successful payment creation"""
    
    mock_payment = Payment(
        id=uuid4().hex,
        organization_id=ORG_ID,
        invoice_id=uuid4().hex,
        amount=150.00,
        payment_method="credit_card",
        status="completed",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "invoice_id": str(uuid4()),
        "amount": 150.00,
        "payment_method": "credit_card",
        "transaction_id": "TXN-123456"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.payment.Payment.create", return_value=mock_payment):
        response = client.post(
            "/api/v1/payments",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["status"] == "completed"


def test_payment_status_update(client, session, current_user, current_org):
    """Test payment status update to failed"""
    
    mock_payment = Payment(
        id=uuid4().hex,
        organization_id=ORG_ID,
        status="failed",
        amount=150.00
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.payment.Payment.update", return_value=mock_payment):
        response = client.patch(
            f"/api/v1/payments/{mock_payment.id}",
            headers=headers,
            json={"status": "failed"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "failed"
