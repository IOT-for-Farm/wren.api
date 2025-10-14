import pytest, json
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException

from api.utils import helpers
from main import app
from api.v1.models.product import Product
from api.v1.services.product import ProductService
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


payload = {}
params = {}

def mock_product():
    return Product(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Org"),
        organization_id=ORG_ID,
        name="Test Product",
        slug="test-product",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def test_create_product(client, session, current_user, current_org):

    app.dependency_overrides[Product.create] = lambda: mock_product

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_product()

    payload["organization_id"] = current_org.id
    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.create", return_value=mock_data) as mock_create:
        headers = {
            # "Authorization": f'Bearer {test_user["access_token"]}'
            "Authorization": f'Bearer token'
        }
        response = client.post(
            "/api/v1/products", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )

        assert response.status_code == 201


def test_create_product_missing_field(client, session, current_user, current_org):

    app.dependency_overrides[Product.create] = lambda: mock_product

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_product()

    payload["organization_id"] = current_org.id
    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.create", return_value=mock_data) as mock_create:
        headers = {
            # "Authorization": f'Bearer {test_user["access_token"]}'
            "Authorization": f'Bearer token'
        }
        response = client.post(
            "/api/v1/products", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )

        assert response.status_code == 422


def test_create_product_unauthorized(client, session, current_org):

    app.dependency_overrides[Product.create] = lambda: mock_product

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_product()

    payload["organization_id"] = current_org.id
    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.create", return_value=mock_data) as mock_create:
        headers = {
            # "Authorization": f'Bearer {test_user["access_token"]}'
            "Authorization": f'Bearer token'
        }
        response = client.post(
            "/api/v1/products", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )
        
        assert response.status_code == 401


def test_get_products(client, session, current_user, current_org):
    
    mock_data = mock_product()
    app.dependency_overrides[Product.fetch_by_field] = [mock_data]

    params["organization_id"] = current_org.id

    headers = {"Authorization": f'Bearer token'}
    response = client.get(
        "/api/v1/products", 
        headers=headers,
        params=params,
    )
    assert response.status_code == 200


def test_get_products_unauthorized(client, session, current_org):
    
    mock_data = mock_product()
    app.dependency_overrides[Product.fetch_by_field] = [mock_data]

    params["organization_id"] = current_org.id

    headers = {}
    response = client.get(
        "/api/v1/products", 
        headers=headers,
        params=params,
    )
    assert response.status_code == 401


def test_get_product_by_id(client, session, current_user, current_org):
    app.dependency_overrides[Product.fetch_by_id] = lambda: mock_product

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_product()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.fetch_by_id", return_value=mock_data) as mock_delete:
        response = client.get(
            f'/api/v1/products/{mock_data.id}',
            headers={'Authorization': 'Bearer token'},
            params=params
        )

        assert response.status_code == 200


def test_get_product_not_found(client, session, current_user, current_org):

    app.dependency_overrides[Product.fetch_by_id] = lambda: mock_product

    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.fetch_by_id", side_effect=HTTPException(status_code=404, detail="Not found")):
        response = client.get(
            f'/api/v1/products/{uuid4().hex}',
            headers={'Authorization': 'Bearer valid_token'},
            params=params
        )

        assert response.status_code == 404


def test_get_product_unauthorized(client, session, current_org):
    mock_data = mock_product()

    params["organization_id"] = current_org.id

    response = client.get(
        f'/api/v1/products/{mock_data.id}',
        headers={},
        params=params
    )

    assert response.status_code == 401


def test_update_product(client, session, current_user, current_org):

    app.dependency_overrides[Product.update] = lambda: mock_product

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_product()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.update", return_value=mock_data) as mock_delete:
        response = client.patch(
            f'/api/v1/products/{mock_data.id}',
            headers={'Authorization': 'Bearer token'},
            params=params,
            json=payload,
            # data=payload
        )

        assert response.status_code == 200


def test_update_product_not_found(client, session, current_user, current_org):

    app.dependency_overrides[Product.update] = lambda: mock_product

    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.fetch_by_id", side_effect=HTTPException(status_code=404, detail="Not found")):
        response = client.patch(
            f'/api/v1/products/{uuid4().hex}',
            headers={'Authorization': 'Bearer valid_token'},
            params=params,
            json=payload,
            # data=payload
        )

        assert response.status_code == 404


def test_update_product_unauthorized(client, session, current_org):

    mock_data = mock_product()

    params["organization_id"] = current_org.id

    response = client.patch(
        f'/api/v1/products/{mock_data.id}',
        headers={},
        params=params,
        json=payload,
        # data=payload
    )

    assert response.status_code == 401


def test_update_product_missing_field(client, session, current_user, current_org):

    app.dependency_overrides[Product.update] = lambda: mock_product

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_product()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.update", return_value=mock_data) as mock_create:
        headers = {"Authorization": f'Bearer token'}
        response = client.post(
            "/api/v1/products", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )

        assert response.status_code == 422


def test_delete_product(client, session, current_user, current_org):

    app.dependency_overrides[Product.soft_delete] = lambda: None

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_product()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.soft_delete", return_value=mock_data) as mock_delete:
        response = client.delete(
            f'/api/v1/products/{mock_data.id}',
            headers={'Authorization': 'Bearer token'},
            params=params
        )

        assert response.status_code == 200


def test_delete_product_not_found(client, session, current_user, current_org):

    app.dependency_overrides[Product.fetch_by_id] = lambda: mock_product

    params["organization_id"] = current_org.id

    with patch("api.v1.models.product.Product.fetch_by_id", side_effect=HTTPException(status_code=404, detail="Not found")):
        response = client.delete(
            f'/api/v1/products/{uuid4().hex}',
            headers={'Authorization': 'Bearer valid_token'},
            params=params
        )

        assert response.status_code == 404


def test_delete_product_unauthorized(client, session, current_org):

    mock_data = mock_product()

    params["organization_id"] = current_org.id

    response = client.delete(
        f'/api/v1/products/{mock_data.id}',
        headers={},
        params=params
    )

    assert response.status_code == 401


def test_product_model_creation():
    """Test Product model instantiation and basic properties"""
    
    product = Product(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Product"),
        organization_id=ORG_ID,
        name="Test Product Model",
        slug="test-product-model",
        description="A test product for model testing",
        status="published",
        type="physical",
        is_available=True
    )
    
    assert product.name == "Test Product Model"
    assert product.slug == "test-product-model"
    assert product.organization_id == ORG_ID
    assert product.is_available is True
    assert product.status == "published"

