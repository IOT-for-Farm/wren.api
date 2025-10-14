import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.vendor import Vendor
from tests.constants import ORG_ID, USER_ID


def test_vendor_creation_success(client, session, current_user, current_org):
    """Test successful vendor creation"""
    
    mock_vendor = Vendor(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="ABC Supplies",
        contact_email="contact@abcsupplies.com",
        contact_phone="+1234567890",
        address="123 Business St",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "name": "ABC Supplies",
        "contact_email": "contact@abcsupplies.com",
        "contact_phone": "+1234567890",
        "address": "123 Business St"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.vendor.Vendor.create", return_value=mock_vendor):
        response = client.post(
            "/api/v1/vendors",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "ABC Supplies"


def test_vendor_contact_update(client, session, current_user, current_org):
    """Test vendor contact information update"""
    
    mock_vendor = Vendor(
        id=uuid4().hex,
        organization_id=ORG_ID,
        name="ABC Supplies",
        contact_email="newcontact@abcsupplies.com"
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.vendor.Vendor.update", return_value=mock_vendor):
        response = client.patch(
            f"/api/v1/vendors/{mock_vendor.id}",
            headers=headers,
            json={"contact_email": "newcontact@abcsupplies.com"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["contact_email"] == "newcontact@abcsupplies.com"
