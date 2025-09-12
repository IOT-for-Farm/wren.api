#!/bin/bash

base_path="api/v1"
file_name=$1  # e.g., "user"

folders_to_update=("models" "routes" "schemas" "services" "tests")

for folder in "${folders_to_update[@]}"
do 
    target_dir="${base_path}/${folder}"
    target_file="${target_dir}/${file_name}.py"

    mkdir -p "$target_dir"

    if [ -f "$target_file" ]; then
        echo "⚠️  Skipping existing file: $target_file"
        continue
    fi

    # Boilerplate per folder
    case $folder in
        "models")
            cat <<EOF > $target_file
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class ${file_name^}(BaseTableModel):
    __tablename__ = '${file_name}s'


EOF
            ;;
        "routes")
            cat <<EOF > $target_file
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from slowapi.decorator import limiter

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.${file_name} import ${file_name^}
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.${file_name} import ${file_name^}Service
from api.v1.schemas import ${file_name} as ${file_name}_schemas
from api.utils.loggers import create_logger


${file_name}_router = APIRouter(prefix='/${file_name//_/-}s', tags=['${file_name^}'])
logger = create_logger(__name__)

@${file_name}_router.post("", status_code=201, response_model=success_response)
async def create_${file_name}(
    payload: ${file_name}_schemas.${file_name^}Base,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new ${file_name}"""

    ${file_name} = ${file_name^}.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'${file_name^} with id {${file_name}.id} created')

    return success_response(
        message=f"${file_name^} created successfully",
        status_code=201,
        data=${file_name}.to_dict()
    )


@${file_name}_router.get("", status_code=200)
async def get_${file_name}s(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all ${file_name}s"""

    query, ${file_name}s, count = ${file_name^}.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            # 'email': search,
        },
    )
    
    return paginator.build_paginated_response(
        items=[${file_name}.to_dict() for ${file_name} in ${file_name}s],
        endpoint='/${file_name}s',
        page=page,
        size=per_page,
        total=count,
    )


@${file_name}_router.get("/{id}", status_code=200, response_model=success_response)
async def get_${file_name}_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a ${file_name} by ID or unique_id in case ID fails."""

    ${file_name} = ${file_name^}.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched ${file_name} successfully",
        status_code=200,
        data=${file_name}.to_dict()
    )


@${file_name}_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_${file_name}(
    id: str,
    payload: ${file_name}_schemas.Update${file_name^},
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a ${file_name}"""

    ${file_name} = ${file_name^}.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'${file_name^} with id {${file_name}.id} updated')

    return success_response(
        message=f"${file_name^} updated successfully",
        status_code=200,
        data=${file_name}.to_dict()
    )


@${file_name}_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_${file_name}(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a ${file_name}"""

    ${file_name^}.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

EOF
            ;;
        "schemas")
            cat <<EOF > $target_file
from pydantic import BaseModel
from typing import Optional


class ${file_name^}Base(BaseModel):

    unique_id: Optional[str] = None


class Update${file_name^}(BaseModel):

    unique_id: Optional[str] = None


EOF
            ;;
        "services")
            cat <<EOF > $target_file
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.${file_name} import ${file_name^}
from api.v1.schemas import ${file_name} as ${file_name}_schemas


logger = create_logger(__name__)

class ${file_name^//_/-}Service:
    pass
EOF
            ;;
        "tests")
            test_dir="tests/v1"
            target_file="${test_dir}/test_${file_name}.py"
            mkdir -p "$test_dir"

            if [ -f "$target_file" ]; then
                echo "⚠️  Skipping existing file: $target_file"
                continue
            fi

            cat <<EOF > $target_file
import pytest, json
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException

from api.utils import helpers
from main import app
from api.v1.models.${file_name} import ${file_name^}
from api.v1.services.${file_name} import ${file_name^}Service
from tests.constants import ORG_ID, SUPERUSER_ID, USER_ID


payload = {}
params = {}

def mock_${file_name}():
    return ${file_name^}(
        id=uuid4().hex,
        unique_id=helpers.generate_unique_id(name="Test Org"),
        organization_id=ORG_ID,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def test_create_${file_name}(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.create] = lambda: mock_${file_name}

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_${file_name}()

    payload["organization_id"] = current_org.id
    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.create", return_value=mock_data) as mock_create:
        headers = {
            # "Authorization": f'Bearer {test_user["access_token"]}'
            "Authorization": f'Bearer token'
        }
        response = client.post(
            "/api/v1/${file_name//_/-}s", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )

        assert response.status_code == 201


def test_create_${file_name}_missing_field(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.create] = lambda: mock_${file_name}

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_${file_name}()

    payload["organization_id"] = current_org.id
    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.create", return_value=mock_data) as mock_create:
        headers = {
            # "Authorization": f'Bearer {test_user["access_token"]}'
            "Authorization": f'Bearer token'
        }
        response = client.post(
            "/api/v1/${file_name//_/-}s", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )

        assert response.status_code == 422


def test_create_${file_name}_unauthorized(client, session, current_org):

    app.dependency_overrides[${file_name^}.create] = lambda: mock_${file_name}

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_${file_name}()

    payload["organization_id"] = current_org.id
    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.create", return_value=mock_data) as mock_create:
        headers = {
            # "Authorization": f'Bearer {test_user["access_token"]}'
            "Authorization": f'Bearer token'
        }
        response = client.post(
            "/api/v1/${file_name//_/-}s", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )
        
        assert response.status_code == 401


def test_get_${file_name}s(client, session, current_org, current_user):
    
    mock_data = mock_${file_name}()
    app.dependency_overrides[${file_name^}.fetch_by_field] = [mock_data]

    params["organization_id"] = current_org.id

    headers = {"Authorization": f'Bearer token'}
    response = client.get(
        "/api/v1/${file_name//_/-}s", 
        headers=headers,
        params=params,
    )
    assert response.status_code == 200


def test_get_${file_name}s_unauthorized(client, session, current_org):
    
    mock_data = mock_${file_name}()
    app.dependency_overrides[${file_name^}.fetch_by_field] = [mock_data]

    params["organization_id"] = current_org.id

    headers = {}
    response = client.get(
        "/api/v1/${file_name//_/-}s", 
        headers=headers,
        params=params,
    )
    assert response.status_code == 401


def test_get_${file_name}_by_id(client, session, current_org, current_user):
    app.dependency_overrides[${file_name^}.fetch_by_id] = lambda: mock_${file_name}

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_${file_name}()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.fetch_by_id", return_value=mock_data) as mock_delete:
        response = client.get(
            f'/api/v1/${file_name//_/-}s/{mock_data.id}',
            headers={'Authorization': 'Bearer token'},
            params=params
        )

        assert response.status_code == 200


def test_get_${file_name}_not_found(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.fetch_by_id] = lambda: mock_${file_name}

    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.fetch_by_id", side_effect=HTTPException(status_code=404, detail="Not found")):
        response = client.get(
            f'/api/v1/${file_name//_/-}s/{uuid4().hex}',
            headers={'Authorization': 'Bearer valid_token'},
            params=params
        )

        assert response.status_code == 404


def test_get_${file_name}_unauthorized(client, session, current_org):
    mock_data = mock_${file_name}()

    params["organization_id"] = current_org.id

    response = client.get(
        f'/api/v1/${file_name//_/-}s/{mock_data.id}',
        headers={},
        params=params
    )

    assert response.status_code == 401


def test_update_${file_name}(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.update] = lambda: mock_${file_name}

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_${file_name}()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.update", return_value=mock_data) as mock_delete:
        response = client.patch(
            f'/api/v1/${file_name//_/-}s/{mock_data.id}',
            headers={'Authorization': 'Bearer token'},
            params=params,
            json=payload,
            # data=payload
        )

        assert response.status_code == 200


def test_update_${file_name}_not_found(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.update] = lambda: mock_${file_name}

    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.fetch_by_id", side_effect=HTTPException(status_code=404, detail="Not found")):
        response = client.patch(
            f'/api/v1/${file_name//_/-}s/{uuid4().hex}',
            headers={'Authorization': 'Bearer valid_token'},
            params=params,
            json=payload,
            # data=payload
        )

        assert response.status_code == 404


def test_update_${file_name}_unauthorized(client, session, current_org):

    mock_data = mock_${file_name}()

    params["organization_id"] = current_org.id

    response = client.patch(
        f'/api/v1/${file_name//_/-}s/{mock_data.id}',
        headers={},
        params=params,
        json=payload,
        # data=payload
    )

    assert response.status_code == 401


def test_update_${file_name}_missing_field(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.update] = lambda: mock_${file_name}

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_${file_name}()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.update", return_value=mock_data) as mock_create:
        headers = {"Authorization": f'Bearer token'}
        response = client.post(
            "/api/v1/${file_name//_/-}s", 
            headers=headers, 
            json=payload,
            # data=payload,  # uncomment if using formdata
            params=params
        )

        assert response.status_code == 422


def test_delete_${file_name}(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.soft_delete] = lambda: None

    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    mock_data = mock_${file_name}()

    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.soft_delete", return_value=mock_data) as mock_delete:
        response = client.delete(
            f'/api/v1/${file_name//_/-}s/{mock_data.id}',
            headers={'Authorization': 'Bearer token'},
            params=params
        )

        assert response.status_code == 200


def test_delete_${file_name}_not_found(client, session, current_org, current_user):

    app.dependency_overrides[${file_name^}.fetch_by_id] = lambda: mock_${file_name}

    params["organization_id"] = current_org.id

    with patch("api.v1.models.${file_name}.${file_name^}.fetch_by_id", side_effect=HTTPException(status_code=404, detail="Not found")):
        response = client.delete(
            f'/api/v1/${file_name//_/-}s/{uuid4().hex}',
            headers={'Authorization': 'Bearer valid_token'},
            params=params
        )

        assert response.status_code == 404


def test_delete_${file_name}_unauthorized(client, session, current_org):

    mock_data = mock_${file_name}()

    params["organization_id"] = current_org.id

    response = client.delete(
        f'/api/v1/${file_name//_/-}s/{mock_data.id}',
        headers={},
        params=params
    )

    assert response.status_code == 401

EOF
            ;;
        *)
            echo "# Empty boilerplate" > "$target_file"
            ;;
    esac
    
    echo "✅ Created: $target_file"

done

echo "🚀 Done creating module: $file_name"
