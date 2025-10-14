import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.customer import Customer
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_customer():
    return Customer(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Customer"),
        organization_id=ORG_ID,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="+1234567890",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_customer(client, session, current_user, current_org):
    """Test creating a new customer successfully"""
    
    app.dependency_overrides[Customer.create] = lambda: mock_customer

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_customer()

    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone_number": "+1987654321"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.customer.Customer.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/customers", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["first_name"] == payload["first_name"]
