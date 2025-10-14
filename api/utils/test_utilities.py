"""
Testing Utilities for Wren API

This module provides comprehensive testing utilities including test data factories,
mock services, test database management, and testing helpers.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from typing import Any, Dict, List, Optional, Union, Type, Callable
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import factory
from factory.fuzzy import FuzzyText, FuzzyInteger, FuzzyChoice
import faker
from faker import Faker
import uuid
import random
import string

from api.utils.loggers import create_logger
from api.db.database import get_db, Base
from api.v1.models.user import User
from api.v1.models.organization import Organization
from api.v1.models.product import Product
from api.v1.models.customer import Customer
from api.v1.models.vendor import Vendor
from api.v1.models.invoice import Invoice
from api.v1.models.order import Order
from api.v1.models.payment import Payment

logger = create_logger(__name__)
fake = Faker()


class TestDatabaseManager:
    """Test database management utilities"""
    
    def __init__(self):
        self.test_db_url = "sqlite:///./test.db"
        self.engine = None
        self.SessionLocal = None
        self.test_db_path = None
    
    def setup_test_database(self):
        """Setup test database"""
        # Create in-memory SQLite database for testing
        self.engine = create_engine(
            self.test_db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info("Test database setup completed")
    
    def teardown_test_database(self):
        """Teardown test database"""
        if self.engine:
            Base.metadata.drop_all(bind=self.engine)
            self.engine.dispose()
        
        logger.info("Test database teardown completed")
    
    def get_test_session(self) -> Session:
        """Get test database session"""
        return self.SessionLocal()
    
    def clear_test_data(self):
        """Clear all test data"""
        with self.engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            
            # Clear all tables
            for table in tables:
                if table != 'sqlite_sequence':  # Skip SQLite system table
                    conn.execute(text(f"DELETE FROM {table}"))
            
            conn.commit()
        
        logger.info("Test data cleared")


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user_data(**kwargs) -> Dict[str, Any]:
        """Create user test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "username": fake.user_name(),
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_organization_data(**kwargs) -> Dict[str, Any]:
        """Create organization test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "name": fake.company(),
            "slug": fake.slug(),
            "description": fake.text(max_nb_chars=200),
            "website": fake.url(),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_product_data(**kwargs) -> Dict[str, Any]:
        """Create product test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "name": fake.catch_phrase(),
            "description": fake.text(max_nb_chars=500),
            "slug": fake.slug(),
            "price": round(random.uniform(10.0, 1000.0), 2),
            "stock_quantity": random.randint(0, 1000),
            "is_available": True,
            "status": "active",
            "type": random.choice(["physical", "digital", "service"]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_customer_data(**kwargs) -> Dict[str, Any]:
        """Create customer test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": fake.phone_number(),
            "address": fake.address(),
            "city": fake.city(),
            "state": fake.state(),
            "zip_code": fake.zipcode(),
            "country": fake.country(),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_vendor_data(**kwargs) -> Dict[str, Any]:
        """Create vendor test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "company_name": fake.company(),
            "contact_name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "address": fake.address(),
            "city": fake.city(),
            "state": fake.state(),
            "zip_code": fake.zipcode(),
            "country": fake.country(),
            "tax_id": fake.ssn(),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_invoice_data(**kwargs) -> Dict[str, Any]:
        """Create invoice test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "invoice_number": fake.bothify(text="INV-####-????"),
            "total_amount": round(random.uniform(100.0, 10000.0), 2),
            "tax_amount": round(random.uniform(10.0, 1000.0), 2),
            "status": random.choice(["draft", "sent", "paid", "overdue", "cancelled"]),
            "due_date": fake.future_date(end_date="+30d"),
            "issue_date": fake.date_between(start_date="-30d", end_date="today"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_order_data(**kwargs) -> Dict[str, Any]:
        """Create order test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "order_number": fake.bothify(text="ORD-####-????"),
            "total_amount": round(random.uniform(50.0, 5000.0), 2),
            "status": random.choice(["pending", "processing", "shipped", "delivered", "cancelled"]),
            "shipping_address": fake.address(),
            "billing_address": fake.address(),
            "notes": fake.text(max_nb_chars=200),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_payment_data(**kwargs) -> Dict[str, Any]:
        """Create payment test data"""
        default_data = {
            "id": str(uuid.uuid4()),
            "amount": round(random.uniform(10.0, 1000.0), 2),
            "payment_method": random.choice(["credit_card", "debit_card", "bank_transfer", "cash", "check"]),
            "status": random.choice(["pending", "completed", "failed", "refunded"]),
            "transaction_id": fake.bothify(text="TXN-####-????"),
            "gateway_response": json.dumps({"status": "success", "code": "200"}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data


class MockService:
    """Mock service utilities"""
    
    @staticmethod
    def mock_email_service():
        """Mock email service"""
        mock_service = Mock()
        mock_service.send_email.return_value = {"status": "sent", "message_id": str(uuid.uuid4())}
        mock_service.send_bulk_email.return_value = {"status": "sent", "count": 10}
        return mock_service
    
    @staticmethod
    def mock_file_service():
        """Mock file service"""
        mock_service = Mock()
        mock_service.upload_file.return_value = {
            "file_id": str(uuid.uuid4()),
            "url": "https://example.com/files/test.jpg",
            "size": 1024
        }
        mock_service.delete_file.return_value = {"status": "deleted"}
        mock_service.get_file_url.return_value = "https://example.com/files/test.jpg"
        return mock_service
    
    @staticmethod
    def mock_payment_gateway():
        """Mock payment gateway"""
        mock_gateway = Mock()
        mock_gateway.process_payment.return_value = {
            "transaction_id": str(uuid.uuid4()),
            "status": "success",
            "amount": 100.0,
            "currency": "USD"
        }
        mock_gateway.refund_payment.return_value = {
            "refund_id": str(uuid.uuid4()),
            "status": "success",
            "amount": 50.0
        }
        return mock_gateway
    
    @staticmethod
    def mock_analytics_service():
        """Mock analytics service"""
        mock_service = Mock()
        mock_service.track_event.return_value = {"status": "tracked"}
        mock_service.get_metrics.return_value = {
            "page_views": 1000,
            "unique_visitors": 500,
            "conversion_rate": 0.05
        }
        return mock_service
    
    @staticmethod
    def mock_notification_service():
        """Mock notification service"""
        mock_service = Mock()
        mock_service.send_notification.return_value = {
            "notification_id": str(uuid.uuid4()),
            "status": "sent"
        }
        mock_service.send_push_notification.return_value = {
            "notification_id": str(uuid.uuid4()),
            "status": "sent"
        }
        return mock_service


class TestClientManager:
    """Test client management utilities"""
    
    def __init__(self, app):
        self.app = app
        self.client = TestClient(app)
        self.auth_tokens = {}
    
    def authenticate_user(self, user_id: str = None) -> str:
        """Authenticate user and return token"""
        if user_id in self.auth_tokens:
            return self.auth_tokens[user_id]
        
        # Create mock token
        token = f"test_token_{user_id or str(uuid.uuid4())}"
        self.auth_tokens[user_id or "default"] = token
        
        return token
    
    def get_auth_headers(self, user_id: str = None) -> Dict[str, str]:
        """Get authentication headers"""
        token = self.authenticate_user(user_id)
        return {"Authorization": f"Bearer {token}"}
    
    def make_authenticated_request(
        self,
        method: str,
        url: str,
        user_id: str = None,
        **kwargs
    ):
        """Make authenticated request"""
        headers = self.get_auth_headers(user_id)
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        return getattr(self.client, method.lower())(url, **kwargs)
    
    def create_test_user(self, **user_data) -> Dict[str, Any]:
        """Create test user via API"""
        user_data = TestDataFactory.create_user_data(**user_data)
        response = self.client.post("/api/v1/users", json=user_data)
        assert response.status_code == 201
        return response.json()["data"]
    
    def create_test_organization(self, **org_data) -> Dict[str, Any]:
        """Create test organization via API"""
        org_data = TestDataFactory.create_organization_data(**org_data)
        response = self.client.post("/api/v1/organizations", json=org_data)
        assert response.status_code == 201
        return response.json()["data"]


class TestAssertions:
    """Custom test assertions"""
    
    @staticmethod
    def assert_response_success(response, expected_status: int = 200):
        """Assert response is successful"""
        assert response.status_code == expected_status
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        return data
    
    @staticmethod
    def assert_response_error(response, expected_status: int = 400):
        """Assert response is an error"""
        assert response.status_code == expected_status
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        return data
    
    @staticmethod
    def assert_paginated_response(response, expected_count: int = None):
        """Assert response is paginated"""
        data = response.json()
        assert "pagination" in data
        assert "data" in data
        assert isinstance(data["data"], list)
        
        if expected_count is not None:
            assert len(data["data"]) == expected_count
        
        return data
    
    @staticmethod
    def assert_model_fields(model_data: Dict[str, Any], required_fields: List[str]):
        """Assert model has required fields"""
        for field in required_fields:
            assert field in model_data, f"Field '{field}' is missing"
    
    @staticmethod
    def assert_datetime_field(field_value: str):
        """Assert field is valid datetime"""
        try:
            datetime.fromisoformat(field_value.replace('Z', '+00:00'))
        except ValueError:
            assert False, f"Invalid datetime format: {field_value}"


class TestFixtures:
    """Test fixtures and utilities"""
    
    @staticmethod
    def create_test_database():
        """Create test database fixture"""
        db_manager = TestDatabaseManager()
        db_manager.setup_test_database()
        return db_manager
    
    @staticmethod
    def create_test_client(app):
        """Create test client fixture"""
        return TestClientManager(app)
    
    @staticmethod
    def mock_external_services():
        """Mock external services fixture"""
        with patch('api.core.dependencies.email_sending_service.send_email') as mock_email, \
             patch('api.utils.minio_service.MinioService') as mock_file, \
             patch('api.core.dependencies.celery.queues.email.tasks.send_email_celery') as mock_celery:
            
            mock_email.return_value = {"status": "sent"}
            mock_file.return_value.upload_file.return_value = {"url": "test_url"}
            mock_celery.delay.return_value = Mock()
            
            yield {
                "email": mock_email,
                "file": mock_file,
                "celery": mock_celery
            }
    
    @staticmethod
    def create_test_data(session: Session, count: int = 10) -> Dict[str, List[Any]]:
        """Create test data in database"""
        test_data = {
            "users": [],
            "organizations": [],
            "products": [],
            "customers": [],
            "vendors": [],
            "invoices": [],
            "orders": [],
            "payments": []
        }
        
        # Create organizations
        for _ in range(count):
            org_data = TestDataFactory.create_organization_data()
            org = Organization(**org_data)
            session.add(org)
            test_data["organizations"].append(org)
        
        session.commit()
        
        # Create users
        for _ in range(count):
            user_data = TestDataFactory.create_user_data()
            user = User(**user_data)
            session.add(user)
            test_data["users"].append(user)
        
        session.commit()
        
        # Create products
        for _ in range(count):
            product_data = TestDataFactory.create_product_data()
            product = Product(**product_data)
            session.add(product)
            test_data["products"].append(product)
        
        session.commit()
        
        # Create customers
        for _ in range(count):
            customer_data = TestDataFactory.create_customer_data()
            customer = Customer(**customer_data)
            session.add(customer)
            test_data["customers"].append(customer)
        
        session.commit()
        
        # Create vendors
        for _ in range(count):
            vendor_data = TestDataFactory.create_vendor_data()
            vendor = Vendor(**vendor_data)
            session.add(vendor)
            test_data["vendors"].append(vendor)
        
        session.commit()
        
        # Create invoices
        for _ in range(count):
            invoice_data = TestDataFactory.create_invoice_data()
            invoice = Invoice(**invoice_data)
            session.add(invoice)
            test_data["invoices"].append(invoice)
        
        session.commit()
        
        # Create orders
        for _ in range(count):
            order_data = TestDataFactory.create_order_data()
            order = Order(**order_data)
            session.add(order)
            test_data["orders"].append(order)
        
        session.commit()
        
        # Create payments
        for _ in range(count):
            payment_data = TestDataFactory.create_payment_data()
            payment = Payment(**payment_data)
            session.add(payment)
            test_data["payments"].append(payment)
        
        session.commit()
        
        return test_data


class PerformanceTestUtils:
    """Performance testing utilities"""
    
    @staticmethod
    def measure_response_time(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Measure function response time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        return {
            "result": result,
            "response_time": end_time - start_time,
            "start_time": start_time,
            "end_time": end_time
        }
    
    @staticmethod
    def benchmark_endpoint(client: TestClient, method: str, url: str, iterations: int = 100, **kwargs):
        """Benchmark API endpoint"""
        response_times = []
        errors = 0
        
        for _ in range(iterations):
            start_time = time.time()
            response = getattr(client, method.lower())(url, **kwargs)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            
            if response.status_code >= 400:
                errors += 1
        
        return {
            "iterations": iterations,
            "errors": errors,
            "success_rate": (iterations - errors) / iterations,
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "response_times": response_times
        }
    
    @staticmethod
    def load_test_endpoint(client: TestClient, method: str, url: str, concurrent_users: int = 10, requests_per_user: int = 10):
        """Load test API endpoint"""
        import concurrent.futures
        import threading
        
        results = []
        errors = 0
        
        def make_requests():
            user_errors = 0
            user_times = []
            
            for _ in range(requests_per_user):
                start_time = time.time()
                try:
                    response = getattr(client, method.lower())(url)
                    if response.status_code >= 400:
                        user_errors += 1
                except Exception:
                    user_errors += 1
                
                end_time = time.time()
                user_times.append(end_time - start_time)
            
            return user_times, user_errors
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_requests) for _ in range(concurrent_users)]
            
            for future in concurrent.futures.as_completed(futures):
                user_times, user_errors = future.result()
                results.extend(user_times)
                errors += user_errors
        
        total_requests = concurrent_users * requests_per_user
        
        return {
            "total_requests": total_requests,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "errors": errors,
            "success_rate": (total_requests - errors) / total_requests,
            "avg_response_time": sum(results) / len(results),
            "min_response_time": min(results),
            "max_response_time": max(results),
            "response_times": results
        }


# Global test utilities
test_db_manager = TestDatabaseManager()
test_data_factory = TestDataFactory()
mock_service = MockService()
test_assertions = TestAssertions()
test_fixtures = TestFixtures()
performance_utils = PerformanceTestUtils()
