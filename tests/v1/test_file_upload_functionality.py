import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from api.v1.models.file import File
from tests.constants import ORG_ID, USER_ID


def test_file_upload_success(client, session, current_user, current_org):
    """Test successful file upload"""
    
    mock_file = File(
        id=uuid4().hex,
        organization_id=ORG_ID,
        model_type="product",
        model_id=uuid4().hex,
        filename="test_image.jpg",
        file_path="/uploads/test_image.jpg",
        file_size=1024000,
        mime_type="image/jpeg",
        created_by=USER_ID,
        created_at=datetime.now(timezone.utc)
    )
    
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None
    
    payload = {
        "model_type": "product",
        "model_id": str(uuid4()),
        "filename": "test_image.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg"
    }
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.file.File.create", return_value=mock_file):
        response = client.post(
            "/api/v1/files",
            headers=headers,
            json=payload,
            params=params
        )
        
        assert response.status_code == 201
        assert response.json()["data"]["filename"] == "test_image.jpg"


def test_file_download_access(client, session, current_user, current_org):
    """Test file download access"""
    
    mock_file = File(
        id=uuid4().hex,
        organization_id=ORG_ID,
        filename="test_image.jpg",
        file_path="/uploads/test_image.jpg",
        is_public=True
    )
    
    params = {"organization_id": current_org.id}
    headers = {"Authorization": "Bearer token"}
    
    with patch("api.v1.models.file.File.fetch_by_id", return_value=mock_file):
        response = client.get(
            f"/api/v1/files/{mock_file.id}",
            headers=headers,
            params=params
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["filename"] == "test_image.jpg"
