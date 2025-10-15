"""
Test Helpers for Wren API

This module provides additional test helpers including database fixtures,
API testing utilities, and integration test helpers.
"""

import pytest
import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import random
import string

from api.utils.loggers import create_logger
from api.utils.test_utilities import TestDataFactory, TestClientManager, TestAssertions
from api.v1.models.user import User
from api.v1.models.organization import Organization
from api.v1.models.product import Product
from api.v1.models.customer import Customer
from api.v1.models.vendor import Vendor
from api.v1.models.invoice import Invoice
from api.v1.models.order import Order
from api.v1.models.payment import Payment

logger = create_logger(__name__)


class DatabaseTestHelper:
    """Database testing helper utilities"""
    
    @staticmethod
    def create_test_user(session: Session, **kwargs) -> User:
        """Create test user in database"""
        user_data = TestDataFactory.create_user_data(**kwargs)
        user = User(**user_data)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def create_test_organization(session: Session, **kwargs) -> Organization:
        """Create test organization in database"""
        org_data = TestDataFactory.create_organization_data(**kwargs)
        organization = Organization(**org_data)
        session.add(organization)
        session.commit()
        session.refresh(organization)
        return organization
    
    @staticmethod
    def create_test_product(session: Session, **kwargs) -> Product:
        """Create test product in database"""
        product_data = TestDataFactory.create_product_data(**kwargs)
        product = Product(**product_data)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    
    @staticmethod
    def create_test_customer(session: Session, **kwargs) -> Customer:
        """Create test customer in database"""
        customer_data = TestDataFactory.create_customer_data(**kwargs)
        customer = Customer(**customer_data)
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer
    
    @staticmethod
    def create_test_vendor(session: Session, **kwargs) -> Vendor:
        """Create test vendor in database"""
        vendor_data = TestDataFactory.create_vendor_data(**kwargs)
        vendor = Vendor(**vendor_data)
        session.add(vendor)
        session.commit()
        session.refresh(vendor)
        return vendor
    
    @staticmethod
    def create_test_invoice(session: Session, **kwargs) -> Invoice:
        """Create test invoice in database"""
        invoice_data = TestDataFactory.create_invoice_data(**kwargs)
        invoice = Invoice(**invoice_data)
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        return invoice
    
    @staticmethod
    def create_test_order(session: Session, **kwargs) -> Order:
        """Create test order in database"""
        order_data = TestDataFactory.create_order_data(**kwargs)
        order = Order(**order_data)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order
    
    @staticmethod
    def create_test_payment(session: Session, **kwargs) -> Payment:
        """Create test payment in database"""
        payment_data = TestDataFactory.create_payment_data(**kwargs)
        payment = Payment(**payment_data)
        session.add(payment)
        session.commit()
        session.refresh(payment)
        return payment
    
    @staticmethod
    def clear_all_tables(session: Session):
        """Clear all tables in test database"""
        # Get all table names
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        
        # Clear all tables
        for table in tables:
            if table != 'sqlite_sequence':  # Skip SQLite system table
                session.execute(text(f"DELETE FROM {table}"))
        
        session.commit()
        logger.info("All test tables cleared")
    
    @staticmethod
    def count_records(session: Session, model_class) -> int:
        """Count records in a table"""
        return session.query(model_class).count()
    
    @staticmethod
    def get_all_records(session: Session, model_class) -> List[Any]:
        """Get all records from a table"""
        return session.query(model_class).all()


class APITestHelper:
    """API testing helper utilities"""
    
    def __init__(self, client: TestClient):
        self.client = client
        self.client_manager = TestClientManager(client.app)
    
    def create_authenticated_user(self, **user_data) -> Dict[str, Any]:
        """Create authenticated user and return user data"""
        user_data = TestDataFactory.create_user_data(**user_data)
        response = self.client.post("/api/v1/users", json=user_data)
        TestAssertions.assert_response_success(response, 201)
        return response.json()["data"]
    
    def create_authenticated_organization(self, **org_data) -> Dict[str, Any]:
        """Create authenticated organization and return org data"""
        org_data = TestDataFactory.create_organization_data(**org_data)
        response = self.client.post("/api/v1/organizations", json=org_data)
        TestAssertions.assert_response_success(response, 201)
        return response.json()["data"]
    
    def make_authenticated_request(
        self,
        method: str,
        url: str,
        user_id: str = None,
        **kwargs
    ):
        """Make authenticated API request"""
        return self.client_manager.make_authenticated_request(method, url, user_id, **kwargs)
    
    def test_crud_operations(
        self,
        endpoint: str,
        create_data: Dict[str, Any],
        update_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Test CRUD operations for an endpoint"""
        results = {}
        
        # Test CREATE
        response = self.make_authenticated_request("POST", endpoint, user_id, json=create_data)
        TestAssertions.assert_response_success(response, 201)
        created_item = response.json()["data"]
        results["created"] = created_item
        
        item_id = created_item["id"]
        
        # Test READ
        response = self.make_authenticated_request("GET", f"{endpoint}/{item_id}", user_id)
        TestAssertions.assert_response_success(response, 200)
        results["read"] = response.json()["data"]
        
        # Test UPDATE
        response = self.make_authenticated_request("PATCH", f"{endpoint}/{item_id}", user_id, json=update_data)
        TestAssertions.assert_response_success(response, 200)
        results["updated"] = response.json()["data"]
        
        # Test DELETE
        response = self.make_authenticated_request("DELETE", f"{endpoint}/{item_id}", user_id)
        TestAssertions.assert_response_success(response, 200)
        results["deleted"] = True
        
        # Verify deletion
        response = self.make_authenticated_request("GET", f"{endpoint}/{item_id}", user_id)
        assert response.status_code == 404
        
        return results
    
    def test_pagination(
        self,
        endpoint: str,
        user_id: str = None,
        expected_count: int = None
    ) -> Dict[str, Any]:
        """Test pagination for an endpoint"""
        results = {}
        
        # Test first page
        response = self.make_authenticated_request("GET", f"{endpoint}?page=1&per_page=5", user_id)
        TestAssertions.assert_paginated_response(response)
        first_page = response.json()
        results["first_page"] = first_page
        
        # Test second page
        response = self.make_authenticated_request("GET", f"{endpoint}?page=2&per_page=5", user_id)
        TestAssertions.assert_paginated_response(response)
        second_page = response.json()
        results["second_page"] = second_page
        
        # Verify different data
        first_page_ids = [item["id"] for item in first_page["data"]]
        second_page_ids = [item["id"] for item in second_page["data"]]
        assert not set(first_page_ids).intersection(set(second_page_ids))
        
        # Test invalid page
        response = self.make_authenticated_request("GET", f"{endpoint}?page=0", user_id)
        assert response.status_code == 400
        
        return results
    
    def test_validation_errors(
        self,
        endpoint: str,
        invalid_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Test validation errors for an endpoint"""
        response = self.make_authenticated_request("POST", endpoint, user_id, json=invalid_data)
        TestAssertions.assert_response_error(response, 422)
        return response.json()
    
    def test_authentication_required(self, endpoint: str, method: str = "GET", **kwargs):
        """Test that authentication is required for an endpoint"""
        response = getattr(self.client, method.lower())(endpoint, **kwargs)
        assert response.status_code == 401
        return response.json()
    
    def test_permission_required(
        self,
        endpoint: str,
        method: str = "GET",
        user_id: str = None,
        **kwargs
    ):
        """Test that proper permissions are required for an endpoint"""
        response = self.make_authenticated_request(method, endpoint, user_id, **kwargs)
        assert response.status_code == 403
        return response.json()


class IntegrationTestHelper:
    """Integration testing helper utilities"""
    
    def __init__(self, client: TestClient, session: Session):
        self.client = client
        self.session = session
        self.api_helper = APITestHelper(client)
        self.db_helper = DatabaseTestHelper()
    
    def setup_integration_test_data(self) -> Dict[str, Any]:
        """Setup comprehensive test data for integration tests"""
        test_data = {}
        
        # Create organization
        organization = self.db_helper.create_test_organization()
        test_data["organization"] = organization
        
        # Create users
        admin_user = self.db_helper.create_test_user(
            email="admin@test.com",
            is_superuser=True,
            organization_id=organization.id
        )
        regular_user = self.db_helper.create_test_user(
            email="user@test.com",
            is_superuser=False,
            organization_id=organization.id
        )
        test_data["admin_user"] = admin_user
        test_data["regular_user"] = regular_user
        
        # Create products
        products = []
        for i in range(5):
            product = self.db_helper.create_test_product(
                name=f"Test Product {i+1}",
                organization_id=organization.id
            )
            products.append(product)
        test_data["products"] = products
        
        # Create customers
        customers = []
        for i in range(3):
            customer = self.db_helper.create_test_customer(
                email=f"customer{i+1}@test.com",
                organization_id=organization.id
            )
            customers.append(customer)
        test_data["customers"] = customers
        
        # Create vendors
        vendors = []
        for i in range(2):
            vendor = self.db_helper.create_test_vendor(
                company_name=f"Test Vendor {i+1}",
                organization_id=organization.id
            )
            vendors.append(vendor)
        test_data["vendors"] = vendors
        
        return test_data
    
    def test_complete_workflow(self, test_data: Dict[str, Any]):
        """Test complete business workflow"""
        results = {}
        
        # Test product creation
        product_data = TestDataFactory.create_product_data(
            organization_id=test_data["organization"].id
        )
        response = self.api_helper.make_authenticated_request(
            "POST", "/api/v1/products", test_data["admin_user"].id, json=product_data
        )
        TestAssertions.assert_response_success(response, 201)
        results["product_created"] = response.json()["data"]
        
        # Test customer creation
        customer_data = TestDataFactory.create_customer_data(
            organization_id=test_data["organization"].id
        )
        response = self.api_helper.make_authenticated_request(
            "POST", "/api/v1/customers", test_data["admin_user"].id, json=customer_data
        )
        TestAssertions.assert_response_success(response, 201)
        results["customer_created"] = response.json()["data"]
        
        # Test order creation
        order_data = TestDataFactory.create_order_data(
            customer_id=results["customer_created"]["id"],
            organization_id=test_data["organization"].id
        )
        response = self.api_helper.make_authenticated_request(
            "POST", "/api/v1/orders", test_data["admin_user"].id, json=order_data
        )
        TestAssertions.assert_response_success(response, 201)
        results["order_created"] = response.json()["data"]
        
        # Test invoice creation
        invoice_data = TestDataFactory.create_invoice_data(
            order_id=results["order_created"]["id"],
            customer_id=results["customer_created"]["id"],
            organization_id=test_data["organization"].id
        )
        response = self.api_helper.make_authenticated_request(
            "POST", "/api/v1/invoices", test_data["admin_user"].id, json=invoice_data
        )
        TestAssertions.assert_response_success(response, 201)
        results["invoice_created"] = response.json()["data"]
        
        # Test payment creation
        payment_data = TestDataFactory.create_payment_data(
            invoice_id=results["invoice_created"]["id"],
            organization_id=test_data["organization"].id
        )
        response = self.api_helper.make_authenticated_request(
            "POST", "/api/v1/payments", test_data["admin_user"].id, json=payment_data
        )
        TestAssertions.assert_response_success(response, 201)
        results["payment_created"] = response.json()["data"]
        
        return results
    
    def test_user_permissions(self, test_data: Dict[str, Any]):
        """Test user permission system"""
        results = {}
        
        # Test admin user can access all endpoints
        admin_endpoints = [
            "/api/v1/users",
            "/api/v1/organizations",
            "/api/v1/products",
            "/api/v1/customers",
            "/api/v1/vendors",
            "/api/v1/orders",
            "/api/v1/invoices",
            "/api/v1/payments"
        ]
        
        for endpoint in admin_endpoints:
            response = self.api_helper.make_authenticated_request(
                "GET", endpoint, test_data["admin_user"].id
            )
            TestAssertions.assert_response_success(response, 200)
        
        results["admin_access"] = True
        
        # Test regular user has limited access
        regular_endpoints = [
            "/api/v1/products",
            "/api/v1/customers"
        ]
        
        for endpoint in regular_endpoints:
            response = self.api_helper.make_authenticated_request(
                "GET", endpoint, test_data["regular_user"].id
            )
            TestAssertions.assert_response_success(response, 200)
        
        # Test regular user cannot access admin endpoints
        admin_only_endpoints = [
            "/api/v1/users",
            "/api/v1/organizations"
        ]
        
        for endpoint in admin_only_endpoints:
            response = self.api_helper.make_authenticated_request(
                "GET", endpoint, test_data["regular_user"].id
            )
            assert response.status_code == 403
        
        results["regular_user_restricted"] = True
        
        return results


class MockExternalServices:
    """Mock external services for testing"""
    
    @staticmethod
    def mock_email_service():
        """Mock email service"""
        with patch('api.core.dependencies.email_sending_service.send_email') as mock:
            mock.return_value = {"status": "sent", "message_id": str(uuid.uuid4())}
            yield mock
    
    @staticmethod
    def mock_file_service():
        """Mock file service"""
        with patch('api.utils.minio_service.MinioService') as mock:
            mock_instance = Mock()
            mock_instance.upload_file.return_value = {
                "file_id": str(uuid.uuid4()),
                "url": "https://example.com/files/test.jpg",
                "size": 1024
            }
            mock_instance.delete_file.return_value = {"status": "deleted"}
            mock.return_value = mock_instance
            yield mock_instance
    
    @staticmethod
    def mock_payment_gateway():
        """Mock payment gateway"""
        with patch('api.v1.services.payment.PaymentGateway') as mock:
            mock_instance = Mock()
            mock_instance.process_payment.return_value = {
                "transaction_id": str(uuid.uuid4()),
                "status": "success",
                "amount": 100.0,
                "currency": "USD"
            }
            mock_instance.refund_payment.return_value = {
                "refund_id": str(uuid.uuid4()),
                "status": "success",
                "amount": 50.0
            }
            mock.return_value = mock_instance
            yield mock_instance
    
    @staticmethod
    def mock_analytics_service():
        """Mock analytics service"""
        with patch('api.utils.analytics.AnalyticsService') as mock:
            mock_instance = Mock()
            mock_instance.track_event.return_value = {"status": "tracked"}
            mock_instance.get_metrics.return_value = {
                "page_views": 1000,
                "unique_visitors": 500,
                "conversion_rate": 0.05
            }
            mock.return_value = mock_instance
            yield mock_instance
    
    @staticmethod
    def mock_notification_service():
        """Mock notification service"""
        with patch('api.utils.notifications.NotificationService') as mock:
            mock_instance = Mock()
            mock_instance.send_notification.return_value = {
                "notification_id": str(uuid.uuid4()),
                "status": "sent"
            }
            mock_instance.send_push_notification.return_value = {
                "notification_id": str(uuid.uuid4()),
                "status": "sent"
            }
            mock.return_value = mock_instance
            yield mock_instance


class TestDataCleanup:
    """Test data cleanup utilities"""
    
    @staticmethod
    def cleanup_test_data(session: Session):
        """Clean up all test data"""
        DatabaseTestHelper.clear_all_tables(session)
        logger.info("Test data cleanup completed")
    
    @staticmethod
    def cleanup_test_files():
        """Clean up test files"""
        import os
        import tempfile
        
        # Clean up temporary files
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            if filename.startswith("test_"):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.warning(f"Could not remove test file {file_path}: {e}")
        
        logger.info("Test files cleanup completed")
    
    @staticmethod
    def cleanup_test_database():
        """Clean up test database"""
        from api.utils.test_utilities import test_db_manager
        test_db_manager.teardown_test_database()
        logger.info("Test database cleanup completed")


# Global test helpers
db_test_helper = DatabaseTestHelper()
mock_external_services = MockExternalServices()
test_data_cleanup = TestDataCleanup()
