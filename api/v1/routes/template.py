import json
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.core.dependencies.email_sending_service import send_email
from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.layout import Layout
from api.v1.models.user import User
from api.v1.models.tag import Tag, TagAssociation
from api.v1.models.template import Template
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.tag import TagService
from api.v1.services.template import TemplateService
from api.v1.schemas import template as template_schemas
from api.utils.loggers import create_logger


template_router = APIRouter(prefix='/templates', tags=['Template'])
logger = create_logger(__name__)

@template_router.post("", status_code=201, response_model=success_response)
async def create_template(
    payload: template_schemas.CreateTemplate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new template"""
    
    AuthService.has_org_permission(
        db=db,
        entity=entity,
        permission='template:create',
        organization_id=payload.organization_id
    )
    
    if payload.layout_id:
        # Check that layout exists
        Layout.fetch_one_by_field(db, id=payload.layout_id, organization_id=payload.organization_id)
        
        if not payload.subject:
            raise HTTPException(
                status_code=400,
                detail="Body and subject are required when layout_id is provided"
            )
    
    payload_dict = payload.model_dump(exclude_unset=True, exclude=['tag_ids'])

    template = Template.create(
        db=db,
        **payload_dict
    )

    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=payload.organization_id,
            model_type='templates',
            entity_id=template.id
        )
    
    logger.info(f"Template created with ID: {template.id}")
      
    return success_response(
        message=f"Template created successfully",
        status_code=200,
        data=template.to_dict()
    )


@template_router.get("", status_code=200)
async def get_templates(
    organization_id: str,
    name: str = None,
    feature: str = None,
    tags: str = None,  # comma separated
    is_active: bool = None,
    layout_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all templates"""
    
    AuthService.belongs_to_organization(
        db=db,
        entity=entity,
        organization_id=organization_id
    )

    query, templates, count = Template.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        feature=feature,
        is_active=is_active,
        layout_id=layout_id
    )
    
    # Organization id filter
    query = query.filter(
        or_(
            Template.organization_id == organization_id,
            Template.organization_id == '-1',
            Template.organization_id == None,
        )
    )
    
    # tag_ids = []
    if tags:
        tags_list = [tag.strip() for tag in tags.split(',')]      
        query = (
            query
            .join(TagAssociation, TagAssociation.entity_id==Template.id)
            .join(Tag, Tag.id == TagAssociation.tag_id)
            .filter(Tag.name.in_(tags_list))
        )
        
    templates, count = paginator.paginate_query(query, page, per_page)
    
    return paginator.build_paginated_response(
        items=[template.to_dict() for template in templates],
        endpoint='/templates',
        page=page,
        size=per_page,
        total=count,
    )


@template_router.get("/{id}", status_code=200, response_model=success_response)
async def get_template_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a template by ID or unique_id in case ID fails."""

    template = Template.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        db=db,
        entity=entity,
        organization_id=template.organization_id
    )
    
    return success_response(
        message=f"Fetched template successfully",
        status_code=200,
        data=template.to_dict()
    )


@template_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_template(
    id: str,
    organization_id: str,
    payload: template_schemas.UpdateTemplate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a template"""
    
    AuthService.has_org_permission(
        db=db,
        entity=entity,
        permission='template:update',
        organization_id=organization_id
    )
    
    if payload.layout_id:
        # Check that layout exists
        Layout.fetch_one_by_field(db, id=payload.layout_id, organization_id=organization_id)

    template = Template.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['tag_ids'])
    )
        
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=organization_id,
            model_type='templates',
            entity_id=template.id
        )

    logger.info(f"Template updated with ID: {template.id}")
    
    return success_response(
        message=f"Template updated successfully",
        status_code=200,
        data=template.to_dict()
    )


@template_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_template(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a template"""
    
    AuthService.has_org_permission(
        db=db,
        entity=entity,
        permission='template:delete',
        organization_id=organization_id
    )

    Template.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )


@template_router.post("/{id}/render", status_code=200, response_model=success_response)
async def render_template(
    id: str,
    organization_id: str,
    payload: template_schemas.RenderTemplate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to render a template"""
    
    AuthService.belongs_to_organization(
        db=db,
        entity=entity,
        organization_id=organization_id
    )
    
    # Fetch the template
    template = Template.fetch_by_id(db, id)
    
    # Check if the template belongs to the organization
    if template.organization_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this template"
        )
    
    # Render the template
    html, subject, footer, body = TemplateService.render_template(
        db=db,
        template_id=id,
        context=payload.context
    )
    
    return success_response(
        message=f"Template rendered successfully",
        status_code=200,
        data={
            "html": html,
            "subject": subject,
            "footer": footer,
            "body": body
        }
    )
    

@template_router.post("/{id}/send-email", status_code=200, response_model=success_response)
async def send_email_from_template(
    id: str,
    organization_id: str,
    bg_tasks: BackgroundTasks,
    payload: template_schemas.SendEmail = Form(media_type="multipart/form-data"),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to send an email from a template"""
    
    AuthService.has_org_permission(
        db=db,
        entity=entity,
        permission='email:send',
        organization_id=organization_id
    )
    
    TemplateService.send_email_from_template(
        db=db,
        bg_tasks=bg_tasks,
        organization_id=organization_id,
        template_id=id,
        context=json.loads(payload.context),
        recipients=[recipient.strip() for recipient in payload.recipients.split(',')],
        attachments=payload.attachments
    )
    
    return success_response(
        message=f"Email sent successfully",
        status_code=200
    )
