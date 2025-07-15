import json
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
import sys, os
import warnings

 
warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID
from api.v1.models.apikey import Apikey
from api.v1.models.organization import Organization
from api.v1.models.user import User
from api.v1.schemas.auth import AuthenticatedEntity, EntityType
from api.v1.services.auth import AuthService
from main import app
from api.db.database import get_db


# DB_TYPE = settings.DB_TYPE
# DB_NAME = settings.DB_NAME
# DB_USER = settings.DB_USER
# DB_PASSWORD = settings.DB_PASSWORD
# DB_HOST = settings.DB_HOST
# DB_PORT = settings.DB_PORT

# # TEST_DB_URI = f"{DB_TYPE}+{DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}_test"
# TEST_DB_URI = f"{DB_TYPE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}_test"

# engine = create_engine(TEST_DB_URI)

# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# @pytest.fixture()
# def session():
#     with engine.connect() as conn:
#         conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
#         Base.metadata.drop_all(bind=engine)
#         conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
        
#     # Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)
#     db = TestingSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# @pytest.fixture()
# def client(session):
#     def override_get_db():
#         try:
#             yield session
#         finally:
#             session.close()

#     app.dependency_overrides[get_db] = override_get_db
#     yield TestClient(app)


# @pytest.fixture
# def test_user(client):
#     payload = {
#         "first_name": "meeena",
#         "last_name": "reena",
#         "email": "reena@gmail.com",
#         "password": "password123",
#     }
#     res = client.post("/api/v1/auth/signup", data=json.dumps(payload))

#     new_user = res.json()["data"]
#     new_user["access_token"] = res.json()["access_token"]
#     new_user["email"] = payload["email"]
#     return new_user


# @pytest.fixture
# def test_org(client, test_user):
#     payload = {
#         "name": "Test Org",
#         "email": "test_email@gmail.com",
#         "phone_number": "1234567890",
#         "phone_country_code": "+234",
#     }

#     headers = {"Authorization": "Bearer {}".format(test_user["access_token"])}

#     res = client.post("/api/v1/organizations", data=json.dumps(payload), headers=headers)
#     org = res.json()
#     return org

@pytest.fixture
def session():
    """Fixture to create a mock database session."

    Yields:
        MagicMock: mock database
    """

    with patch("api.db.database.get_db", autospec=True) as mock_get_db:
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        yield mock_db
        
    app.dependency_overrides = {}


# @pytest.fixture
# def client():
#     yield TestClient(app)

@pytest.fixture
def client(session):
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}
    

@pytest.fixture
def current_org():
    organization = Organization(
        id=ORG_ID,
        name="Test Org",
        slug='text-org',
        created_by=USER_ID
    )
    
    return organization
    

@pytest.fixture
def current_user():
    user = User(
        id=USER_ID,
        email="testuser@gmail.com",
        password=AuthService.hash_secret("Testpassword@123"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    
    entity = AuthenticatedEntity(
        type=EntityType.USER,
        entity=user
    )

    app.dependency_overrides[AuthService.get_current_user_entity] = lambda: entity
    return entity
    
@pytest.fixture
def current_superuser():
    user = User(
        id=SUPERUSER_ID,
        email="superuser@gmail.com",
        password=AuthService.hash_secret("Testpassword@123"),
        first_name="Super",
        last_name="User",
        is_active=True,
        is_superuser=True
    )
    
    entity = AuthenticatedEntity(
        type=EntityType.USER,
        entity=user
    )

    app.dependency_overrides[AuthService.get_current_user_entity] = lambda: entity
    return entity
    
# @pytest.fixture
# def current_apikey():
#     apikey = Apikey(
#         id=uuid4().hex,
#         user_id=USER_ID,
#         organization_id=ORG_ID
        
#     )
#     app.dependency_overrides[AuthService.get_current_apikey_entity] = lambda: AuthenticatedEntity(
#         type=EntityType.APIKEY,
#         entity=apikey
#     )

@pytest.fixture(scope='module')
def mock_send_email():
    with patch("api.core.dependencies.email_sending_service.send_email") as mock_email_sending:
        with patch("fastapi.BackgroundTasks.add_task") as add_task_mock:
            add_task_mock.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
            
            yield mock_email_sending