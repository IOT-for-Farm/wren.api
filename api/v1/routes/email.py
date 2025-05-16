import json
from uuid import uuid4
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.email import EmailRegistry
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.email import EmailService
from api.v1.schemas import email as email_schemas
from api.utils.loggers import create_logger
from api.v1.services.file import FileService


email_router = APIRouter(prefix='/emails', tags=['Email'])
logger = create_logger(__name__)

@email_router.post("", status_code=201, response_model=success_response)
async def create_email(
    payload: email_schemas.EmailBase=Form(media_type="multipart/form-data"),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new email"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='email:create',
        organization_id=payload.organization_id
    )
    
    model_id = uuid4().hex
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, organization_id=payload.organization_id
        )
    
    if payload.context:
        payload.context = json.loads(payload.context)
        
    if payload.recipients:
        payload.recipients = [recipient.strip() for recipient in payload.recipients.split(',')]
        
    if payload.attachments:
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=payload.organization_id ,
            model_name='email_attachments',
            model_id=model_id,
        )

    email = EmailRegistry.create(
        db=db,
        **payload.model_dump(exclude_unset=True, exclude=['attachments'])
    )

    return success_response(
        message=f"Email created successfully",
        status_code=201,
        data=email.to_dict()
    )


@email_router.get("", status_code=200)
async def get_emails(
    organization_id: str,
    status: str = None,
    priority: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all emails"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, emails, count = EmailRegistry.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        organization_id=organization_id,
        status=status,
        priority=priority,
    )
    
    return paginator.build_paginated_response(
        items=[email.to_dict() for email in emails],
        endpoint='/emails',
        page=page,
        size=per_page,
        total=count,
    )


@email_router.get("/{id}", status_code=200, response_model=success_response)
async def get_email_by_id(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a email by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    email = EmailRegistry.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched email successfully",
        status_code=200,
        data=email.to_dict()
    )


@email_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_email(
    id: str,
    organization_id: str,
    payload: email_schemas.UpdateEmail=Form(media_type="multipart/form-data"),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a email"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='email:update',
        organization_id=organization_id
    )
    
    if payload.context:
        payload.context = json.loads(payload.context)
        
    if payload.recipients:
        payload.recipients = [recipient.strip() for recipient in payload.recipients.split(',')]
        
    if payload.attachments:
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=organization_id ,
            model_name='email_attachments',
            model_id=id,
        )

    email = EmailRegistry.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['attachments'])
    )

    return success_response(
        message=f"Email updated successfully",
        status_code=200,
        data=email.to_dict()
    )


@email_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_email(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a email"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='email:delete',
        organization_id=organization_id
    )

    EmailRegistry.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )
