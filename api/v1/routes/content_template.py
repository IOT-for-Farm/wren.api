from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.content import ContentTemplate
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.content import ContentService
from api.v1.schemas import content as content_schemas
from api.utils.loggers import create_logger


content_template_router = APIRouter(prefix='/content-templates', tags=['Content Management'])
logger = create_logger(__name__)

@content_template_router.post("", status_code=201, response_model=success_response)
async def create_content_template(
    payload: content_schemas.ContentTemplateBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new content_template"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='content-template:create',
        organization_id=payload.organization_id
    )

    content_template = ContentTemplate.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Content template created successfully",
        status_code=201,
        data=content_template.to_dict()
    )


@content_template_router.get("", status_code=200)
async def get_content_templates(
    organization_id: str,
    name: str = None,
    content_type: str = None,
    is_active: bool = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all content_templates"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, content_templates, count = ContentTemplate.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        content_type=content_type,
        is_active=is_active,
    )
    
    query = query.filter(
        or_(
            ContentTemplate.organization_id==organization_id,
            ContentTemplate.organization_id=='-1',
            ContentTemplate.organization_id==None,
        )
    )
    
    count = query.count()
    content_templates = query.all()
    
    return paginator.build_paginated_response(
        items=[content_template.to_dict() for content_template in content_templates],
        endpoint='/content-templates',
        page=page,
        size=per_page,
        total=count,
    )


@content_template_router.get("/{id}", status_code=200, response_model=success_response)
async def get_content_template_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a content_template by ID or unique_id in case ID fails."""

    content_template = ContentTemplate.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=content_template.organization_id
    )
    
    return success_response(
        message=f"Fetched content_template successfully",
        status_code=200,
        data=content_template.to_dict()
    )


@content_template_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_content_template(
    id: str,
    organization_id: str,
    payload: content_schemas.UpdateContentTemplate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a content_template"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='content-template:update',
        organization_id=organization_id
    )

    content_template = ContentTemplate.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Content template updated successfully",
        status_code=200,
        data=content_template.to_dict()
    )


@content_template_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_content_template(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a content_template"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='content-template:update',
        organization_id=organization_id
    )

    ContentTemplate.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )
