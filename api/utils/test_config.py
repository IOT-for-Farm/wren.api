"""
Test Configuration for Wren API

This module provides test configuration, fixtures, and setup utilities
for comprehensive testing of the Wren API.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from typing import Any, Dict, List, Optional, Generator
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import uuid
import json

from api.utils.loggers import create_logger
from api.utils.test_utilities import TestDatabaseManager, TestDataFactory, TestClientManager
from api.utils.test_helpers import DatabaseTestHelper, APITestHelper, IntegrationTestHelper
from api.db.database import get_db, Base
from main import app

logger = create_logger(__name__)


class TestConfig:
    """Test configuration settings"""
    
    # Database settings
    TEST_DATABASE_URL = "sqlite:///./test.db"
    TEST_DATABASE_IN_MEMORY = True
    
    # API settings
    TEST_API_BASE_URL = "/api/v1"
    TEST_TIMEOUT = 30
    
    # Test data settings
    DEFAULT_TEST_DATA_COUNT = 10
    MAX_TEST_DATA_COUNT = 100
    
    # Performance test settings
    PERFORMANCE_TEST_ITERATIONS = 100
    LOAD_TEST_CONCURRENT_USERS = 10
    LOAD_TEST_REQUESTS_PER_USER = 10
    
    # Mock settings
    MOCK_EXTERNAL_SERVICES = True
    MOCK_EMAIL_SERVICE = True
    MOCK_FILE_SERVICE = True
    MOCK_PAYMENT_GATEWAY = True
    MOCK_ANALYTICS_SERVICE = True
    MOCK_NOTIFICATION_SERVICE = True


class TestFixtures:
    """Test fixtures and setup utilities"""
    
    @staticmethod
    @pytest.fixture(scope="session")
    def test_database():
        """Test database fixture"""
        db_manager = TestDatabaseManager()
        db_manager.setup_test_database()
        yield db_manager
        db_manager.teardown_test_database()
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_session(test_database):
        """Test database session fixture"""
        session = test_database.get_test_session()
        yield session
        session.close()
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_client():
        """Test client fixture"""
        with TestClient(app) as client:
            yield client
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_client_manager(test_client):
        """Test client manager fixture"""
        return TestClientManager(test_client.app)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def api_helper(test_client):
        """API helper fixture"""
        return APITestHelper(test_client)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def db_helper(test_session):
        """Database helper fixture"""
        return DatabaseTestHelper()
    
    @staticmethod
    @pytest.fixture(scope="function")
    def integration_helper(test_client, test_session):
        """Integration test helper fixture"""
        return IntegrationTestHelper(test_client, test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_user(test_session):
        """Test user fixture"""
        return DatabaseTestHelper.create_test_user(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_organization(test_session):
        """Test organization fixture"""
        return DatabaseTestHelper.create_test_organization(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_product(test_session):
        """Test product fixture"""
        return DatabaseTestHelper.create_test_product(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_customer(test_session):
        """Test customer fixture"""
        return DatabaseTestHelper.create_test_customer(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_vendor(test_session):
        """Test vendor fixture"""
        return DatabaseTestHelper.create_test_vendor(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_invoice(test_session):
        """Test invoice fixture"""
        return DatabaseTestHelper.create_test_invoice(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_order(test_session):
        """Test order fixture"""
        return DatabaseTestHelper.create_test_order(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_payment(test_session):
        """Test payment fixture"""
        return DatabaseTestHelper.create_test_payment(test_session)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def test_data(test_session):
        """Test data fixture"""
        return TestDataFactory.create_test_data(test_session, TestConfig.DEFAULT_TEST_DATA_COUNT)
    
    @staticmethod
    @pytest.fixture(scope="function")
    def mock_services():
        """Mock external services fixture"""
        with patch('api.core.dependencies.email_sending_service.send_email') as mock_email, \
             patch('api.utils.minio_service.MinioService') as mock_file, \
             patch('api.core.dependencies.celery.queues.email.tasks.send_email_celery') as mock_celery, \
             patch('api.v1.services.payment.PaymentGateway') as mock_payment, \
             patch('api.utils.analytics.AnalyticsService') as mock_analytics, \
             patch('api.utils.notifications.NotificationService') as mock_notifications:
            
            # Configure mocks
            mock_email.return_value = {"status": "sent", "message_id": str(uuid.uuid4())}
            mock_celery.delay.return_value = Mock()
            
            mock_file_instance = Mock()
            mock_file_instance.upload_file.return_value = {
                "file_id": str(uuid.uuid4()),
                "url": "https://example.com/files/test.jpg",
                "size": 1024
            }
            mock_file_instance.delete_file.return_value = {"status": "deleted"}
            mock_file.return_value = mock_file_instance
            
            mock_payment_instance = Mock()
            mock_payment_instance.process_payment.return_value = {
                "transaction_id": str(uuid.uuid4()),
                "status": "success",
                "amount": 100.0,
                "currency": "USD"
            }
            mock_payment_instance.refund_payment.return_value = {
                "refund_id": str(uuid.uuid4()),
                "status": "success",
                "amount": 50.0
            }
            mock_payment.return_value = mock_payment_instance
            
            mock_analytics_instance = Mock()
            mock_analytics_instance.track_event.return_value = {"status": "tracked"}
            mock_analytics_instance.get_metrics.return_value = {
                "page_views": 1000,
                "unique_visitors": 500,
                "conversion_rate": 0.05
            }
            mock_analytics.return_value = mock_analytics_instance
            
            mock_notifications_instance = Mock()
            mock_notifications_instance.send_notification.return_value = {
                "notification_id": str(uuid.uuid4()),
                "status": "sent"
            }
            mock_notifications_instance.send_push_notification.return_value = {
                "notification_id": str(uuid.uuid4()),
                "status": "sent"
            }
            mock_notifications.return_value = mock_notifications_instance
            
            yield {
                "email": mock_email,
                "file": mock_file_instance,
                "celery": mock_celery,
                "payment": mock_payment_instance,
                "analytics": mock_analytics_instance,
                "notifications": mock_notifications_instance
            }


class TestSuite:
    """Test suite configuration and utilities"""
    
    @staticmethod
    def setup_test_environment():
        """Setup test environment"""
        # Set test environment variables
        os.environ["TESTING"] = "true"
        os.environ["DATABASE_URL"] = TestConfig.TEST_DATABASE_URL
        os.environ["LOG_LEVEL"] = "WARNING"
        
        # Create test directories
        test_dirs = ["tests/temp", "tests/fixtures", "tests/data"]
        for test_dir in test_dirs:
            os.makedirs(test_dir, exist_ok=True)
        
        logger.info("Test environment setup completed")
    
    @staticmethod
    def teardown_test_environment():
        """Teardown test environment"""
        # Clean up test directories
        test_dirs = ["tests/temp", "tests/fixtures", "tests/data"]
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
        
        # Remove test environment variables
        test_env_vars = ["TESTING", "DATABASE_URL", "LOG_LEVEL"]
        for env_var in test_env_vars:
            if env_var in os.environ:
                del os.environ[env_var]
        
        logger.info("Test environment teardown completed")
    
    @staticmethod
    def run_unit_tests():
        """Run unit tests"""
        pytest.main([
            "tests/unit/",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
    
    @staticmethod
    def run_integration_tests():
        """Run integration tests"""
        pytest.main([
            "tests/integration/",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
    
    @staticmethod
    def run_performance_tests():
        """Run performance tests"""
        pytest.main([
            "tests/performance/",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
    
    @staticmethod
    def run_all_tests():
        """Run all tests"""
        pytest.main([
            "tests/",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
    
    @staticmethod
    def run_tests_with_coverage():
        """Run tests with coverage"""
        pytest.main([
            "tests/",
            "-v",
            "--tb=short",
            "--disable-warnings",
            "--cov=api",
            "--cov-report=html",
            "--cov-report=term"
        ])


class TestDataManager:
    """Test data management utilities"""
    
    @staticmethod
    def create_test_dataset(session: Session, count: int = None) -> Dict[str, List[Any]]:
        """Create comprehensive test dataset"""
        if count is None:
            count = TestConfig.DEFAULT_TEST_DATA_COUNT
        
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
            org = DatabaseTestHelper.create_test_organization(session)
            test_data["organizations"].append(org)
        
        # Create users
        for _ in range(count):
            user = DatabaseTestHelper.create_test_user(session)
            test_data["users"].append(user)
        
        # Create products
        for _ in range(count):
            product = DatabaseTestHelper.create_test_product(session)
            test_data["products"].append(product)
        
        # Create customers
        for _ in range(count):
            customer = DatabaseTestHelper.create_test_customer(session)
            test_data["customers"].append(customer)
        
        # Create vendors
        for _ in range(count):
            vendor = DatabaseTestHelper.create_test_vendor(session)
            test_data["vendors"].append(vendor)
        
        # Create invoices
        for _ in range(count):
            invoice = DatabaseTestHelper.create_test_invoice(session)
            test_data["invoices"].append(invoice)
        
        # Create orders
        for _ in range(count):
            order = DatabaseTestHelper.create_test_order(session)
            test_data["orders"].append(order)
        
        # Create payments
        for _ in range(count):
            payment = DatabaseTestHelper.create_test_payment(session)
            test_data["payments"].append(payment)
        
        return test_data
    
    @staticmethod
    def save_test_data_to_file(test_data: Dict[str, List[Any]], filename: str):
        """Save test data to JSON file"""
        serialized_data = {}
        
        for key, items in test_data.items():
            serialized_data[key] = []
            for item in items:
                if hasattr(item, '__dict__'):
                    serialized_data[key].append(item.__dict__)
                else:
                    serialized_data[key].append(item)
        
        with open(filename, 'w') as f:
            json.dump(serialized_data, f, indent=2, default=str)
        
        logger.info(f"Test data saved to {filename}")
    
    @staticmethod
    def load_test_data_from_file(filename: str) -> Dict[str, List[Any]]:
        """Load test data from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Test data loaded from {filename}")
        return data


class TestReportGenerator:
    """Test report generation utilities"""
    
    @staticmethod
    def generate_test_report(test_results: Dict[str, Any]) -> str:
        """Generate test report"""
        report = f"""
# Test Report

## Summary
- Total Tests: {test_results.get('total_tests', 0)}
- Passed: {test_results.get('passed', 0)}
- Failed: {test_results.get('failed', 0)}
- Skipped: {test_results.get('skipped', 0)}
- Success Rate: {test_results.get('success_rate', 0):.2f}%

## Test Categories
"""
        
        for category, results in test_results.get('categories', {}).items():
            report += f"""
### {category}
- Tests: {results.get('total', 0)}
- Passed: {results.get('passed', 0)}
- Failed: {results.get('failed', 0)}
- Success Rate: {results.get('success_rate', 0):.2f}%
"""
        
        report += f"""
## Performance Metrics
- Average Response Time: {test_results.get('avg_response_time', 0):.3f}s
- Max Response Time: {test_results.get('max_response_time', 0):.3f}s
- Min Response Time: {test_results.get('min_response_time', 0):.3f}s

## Coverage
- Code Coverage: {test_results.get('coverage', 0):.2f}%
- Line Coverage: {test_results.get('line_coverage', 0):.2f}%
- Branch Coverage: {test_results.get('branch_coverage', 0):.2f}%

Generated at: {datetime.utcnow().isoformat()}
"""
        
        return report
    
    @staticmethod
    def save_test_report(report: str, filename: str):
        """Save test report to file"""
        with open(filename, 'w') as f:
            f.write(report)
        
        logger.info(f"Test report saved to {filename}")


# Global test configuration
test_config = TestConfig()
test_fixtures = TestFixtures()
test_suite = TestSuite()
test_data_manager = TestDataManager()
test_report_generator = TestReportGenerator()
