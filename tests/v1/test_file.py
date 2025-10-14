import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from api.utils import helpers
from main import app
from api.v1.models.file import File
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


def mock_file():
    return File(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test File"),
        organization_id=ORG_ID,
        model_type="product",
        model_id=uuid4().hex,
        filename="test_file.jpg",
        original_filename="test_image.jpg",
        file_path="/uploads/test_file.jpg",
        file_size=1024000,
        mime_type="image/jpeg",
        is_public=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def test_create_file(client, session, current_user, current_org):
    """Test creating a new file record successfully"""
    
    app.dependency_overrides[File.create] = lambda: mock_file

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_file()

    payload = {
        "model_type": "product",
        "model_id": uuid4().hex,
        "filename": "product_image.jpg",
        "original_filename": "product_photo.jpg",
        "file_path": "/uploads/product_image.jpg",
        "file_size": 2048000,
        "mime_type": "image/jpeg"
    }

    params = {"organization_id": current_org.id}

    with patch("api.v1.models.file.File.create", return_value=mock_data) as mock_create:
        headers = {"Authorization": "Bearer token"}
        response = client.post(
            "/api/v1/files", 
            headers=headers,
            json=payload,
            params=params
        )

        assert response.status_code == 201
        assert response.json()["data"]["filename"] == payload["filename"]
