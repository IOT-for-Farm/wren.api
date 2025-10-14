import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.customer import Customer
from tests.constants import ORG_ID, USER_ID


def test_customer_creation_success(client, session, current_user, current_org):
    """Test successful customer creation"""
    
    mock_customer = Customer(
        id=uuid4().hex,
        organization_id=ORG_ID,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.customer.Customer.create", return_value=mock_customer):
        response = client.post(
            "/api/v1/customers",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["email"] == "john.doe@example.com"


def test_customer_profile_update(client, session, current_user, current_org):
    """Test customer profile update"""
    
    mock_customer = Customer(
        id=uuid4().hex,
        organization_id=ORG_ID,
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com"
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.customer.Customer.update", return_value=mock_customer):
        response = client.patch(
            f"/api/v1/customers/{mock_customer.id}",
            headers=headers,
            json={"first_name": "Jane"},
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["first_name"] == "Jane"
