from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.apikey import Apikey
from api.v1.services.auth import AuthService
from api.v1.services.apikey import ApikeyService
from api.v1.schemas import apikey as apikey_schemas
from api.utils.loggers import create_logger
from api.v1.schemas.auth import AuthenticatedEntity


apikey_router = APIRouter(prefix='/apikeys', tags=['Apikey'])
logger = create_logger(__name__)

@apikey_router.post("", status_code=201, response_model=success_response)
async def create_apikey(
    payload: apikey_schemas.ApikeyBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new apikey"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=payload.organization_id,
        permission='apikey:create',
        db=db
    )

    user: User = entity.entity
    apikey_obj, key = ApikeyService.create(
        db=db,
        payload=payload,
        user_id=user.id
    )

    return success_response(
        message=f"Apikey created successfully",
        status_code=200,
        data={**apikey_obj.to_dict(), 'key': key}
    )


@apikey_router.get("", status_code=200)
async def get_apikeys(
    organization_id: str,
    app_name: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all apikeys"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='apikey:view',
        db=db
    )

    query, apikeys, count = Apikey.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'app_name': app_name,
        },
        organization_id=organization_id
    )
    
    return paginator.build_paginated_response(
        items=[apikey.to_dict(excludes=['key_hash']) for apikey in apikeys],
        endpoint='/apikeys',
        page=page,
        size=per_page,
        total=count,
    )


@apikey_router.get("/{id}", status_code=200, response_model=success_response)
async def get_apikey_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get an apikey by ID or unique_id in case ID fails."""

    apikey = Apikey.fetch_by_id(db, id)
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=apikey.organization_id,
        permission='apikey:view',
        db=db
    )
    
    return success_response(
        message=f"Fetched apikey successfully",
        status_code=200,
        data=apikey.to_dict()
    )


@apikey_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_apikey(
    id: str,
    organization_id: str,
    payload: apikey_schemas.UpdateApikey,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update an apikey"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='apikey:update',
        db=db
    )

    apikey = Apikey.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Apikey updated successfully",
        status_code=200,
        data=apikey.to_dict()
    )


@apikey_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_apikey(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete an apikey"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='apikey:delete',
        db=db
    )

    Apikey.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

