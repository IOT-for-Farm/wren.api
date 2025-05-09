from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.layout import Layout
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.layout import LayoutService
from api.v1.schemas import layout as layout_schemas
from api.utils.loggers import create_logger


layout_router = APIRouter(prefix='/layouts', tags=['Layout'])
logger = create_logger(__name__)

@layout_router.post("", status_code=201, response_model=success_response)
async def create_layout(
    payload: layout_schemas.LayoutBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new layout"""
    
    AuthService.has_org_permission(
        db=db,
        entity=entity,
        permission='layout:create',
        organization_id=payload.organization_id
    )
    
    # Check if the layout already exists
    existing_layout = Layout.fetch_one_by_field(
        db=db,
        throw_error=False,
        organization_id=payload.organization_id,
        name=payload.name,
    )
    
    if existing_layout:
        raise HTTPException(
            status_code=400,
            detail=f"Layout with name '{payload.name}' already exists"
        )

    layout = Layout.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Layout created successfully",
        status_code=200,
        data=layout.to_dict()
    )


@layout_router.get("", status_code=200)
async def get_layouts(
    organization_id: str,
    name: str = None,
    feature: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all layouts"""
    
    AuthService.belongs_to_organization(
        db=db,
        entity=entity,
        organization_id=organization_id
    )

    query, layouts, count = Layout.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        # organization_id=organization_id,
        feature=feature
    )
    
    # Organization id filter
    query = query.filter(
        or_(
            Layout.organization_id == organization_id,
            Layout.organization_id == '-1',
            Layout.organization_id == None,
        )
    )
    
    count = query.count()
    layouts = query.all()
    
    return paginator.build_paginated_response(
        items=[layout.to_dict() for layout in layouts],
        endpoint='/layouts',
        page=page,
        size=per_page,
        total=count,
    )


@layout_router.get("/{id}", status_code=200, response_model=success_response)
async def get_layout_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a layout by ID or unique_id in case ID fails."""

    layout = Layout.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        db=db,
        entity=entity,
        organization_id=layout.organization_id
    )
    
    return success_response(
        message=f"Fetched layout successfully",
        status_code=200,
        data=layout.to_dict()
    )


@layout_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_layout(
    id: str,
    organization_id: str,
    payload: layout_schemas.UpdateLayout,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a layout"""
    
    AuthService.has_org_permission(
        db=db,
        entity=entity,
        permission='layout:update',
        organization_id=organization_id
    )
    
    # Check if the layout exists
    if payload.name:
        existing_layout = Layout.fetch_one_by_field(
            db=db,
            throw_error=False,
            organization_id=organization_id,
            name=payload.name,
        )
        
        if existing_layout and existing_layout.id != id:
            raise HTTPException(
                status_code=400,
                detail=f"Layout with name '{payload.name}' already exists"
            )

    layout = Layout.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Layout updated successfully",
        status_code=200,
        data=layout.to_dict()
    )


@layout_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_layout(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a layout"""
    
    AuthService.has_org_permission(
        db=db,
        entity=entity,
        permission='layout:delete',
        organization_id=organization_id
    )

    Layout.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

