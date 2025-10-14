import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.vendor import Vendor
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_vendor():
    return Vendor(
        id=uuid4().hex,
        business_partner_id=uuid4().hex,
        organization_id=ORG_ID,
        vendor_code="VENDOR001",
        payment_terms="Net 30",
        credit_limit=10000.00,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_vendor(client, session, current_user, current_org):
    """Test creating a new vendor successfully"""
    
    app.dependency_overrides[Vendor.create] = lambda: mock_vendor

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_vendor()

    payload = {
        "business_partner_id": uuid4().hex,
        "vendor_code": "VENDOR002",
        "payment_terms": "Net 15",
        "credit_limit": 5000.00
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.vendor.Vendor.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/vendors", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["vendor_code"] == payload["vendor_code"]
