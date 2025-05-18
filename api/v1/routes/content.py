from datetime import datetime
import json
from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException
from slugify import slugify
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.core.dependencies.celery.queues.general.tasks import generate_content_translations
from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.tag import Tag, TagAssociation
from api.v1.models.user import User
from api.v1.models.content import Content, ContentTemplate, ContentTranslation, ContentVersion
from api.v1.schemas.file import FileBase
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.content import ContentService
from api.v1.schemas import content as content_schemas
from api.utils.loggers import create_logger
from api.v1.services.file import FileService
from api.v1.services.tag import TagService
from config import config


content_router = APIRouter(prefix='/contents', tags=['Content Management'])
logger = create_logger(__name__)

@content_router.post("", status_code=201, response_model=success_response)
async def create_content(
    payload: content_schemas.ContentCreate = Form(media_type='multipart/form-data'),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new content"""
    
    user: User = entity.entity
    
    # generate uuid id because of file upload
    model_id = uuid4().hex
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='content:create',
        organization_id=payload.organization_id
    )
        
    # if payload.publish_date > payload.expiration_date:
    #     raise HTTPException(400, 'Start date cannot be greater than end date')
        
    if payload.cover_image:
        file = await FileService.upload_file(
            db=db,
            payload=FileBase(
                file=payload.cover_image,
                organization_id=payload.organization_id,
                model_name='contents',
                model_id=model_id,
            ),
            allowed_extensions=['jpg', 'png', 'jpeg'],
            add_to_db=False
        )
        payload.cover_image_url = file['url']
    
    if payload.attachments:
        # TODO: bulk upload files. use celery for this
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=payload.organization_id,
            model_name='contents',
            model_id=model_id,
        )
        
    if payload.content_template_id:
        template = ContentTemplate.fetch_by_id(db, payload.content_template_id)
        payload.content_type = template.content_type
    
    if not payload.cover_image_url:
        payload.cover_image_url = helpers.generate_logo_url(payload.title)
    
    if not payload.slug:
        payload.slug = slugify(payload.title)
        
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )
    
    if not payload.seo_title:
        payload.seo_title = payload.title
        
    # if payload.additional_info:
    #     payload.additional_info = helpers.format_additional_info_create(json.loads(payload.additional_info))
    #     print(payload.additional_info)
    
    payload.content_type = payload.content_type if isinstance(payload.content_type, str) else payload.content_type.value
    payload.visibility = payload.visibility.value   
    
    content = Content.create(
        db=db,
        id=model_id,
        author_id=user.id,
        content_url=(
            f"{config('APP_URL')}/contents/{payload.slug}" 
            if not payload.website_base_url 
            else f"{payload.website_base_url}/contents/{payload.slug}"),
        **payload.model_dump(exclude_unset=True, exclude=['cover_image', 'attachments', 'website_base_url', 'tag_ids'])
    )
    
    if payload.tag_ids:
        tag_ids = payload.tag_ids.split(',')
        
        TagService.create_tag_association(
            db=db,
            tag_ids=tag_ids,
            organization_id=payload.organization_id,
            model_type='contents',
            entity_id=content.id
        )
    
    logger.info(f'New content created with name {content.title}')
    
    # Generate translations for the content
    generate_content_translations.delay(content=content.to_dict())
    
    return success_response(
        message=f"Content created successfully",
        status_code=201,
        data=content.to_dict()
    )


@content_router.get("", status_code=200)
async def get_contents(
    organization_id: str,
    title: str = None,
    content_type: str = None,
    is_visible_on_website: bool = None,
    visibility: str = None,
    content_status: str = None,
    review_status: str = None,
    show_visible_only: bool = None,
    slug: str = None,
    tags: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all contents"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, contents, count = Content.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'title': title,
        },
        organization_id=organization_id,
        content_type=content_type,
        is_visible_on_website=is_visible_on_website,
        visibility=visibility,
        content_status=content_status,
        review_status=review_status,
        slug=slug
    )
    
    if show_visible_only:
        now = datetime.now()
        query = query.filter(
            Content.visibility == 'public',
            Content.publish_date <= now,
            or_(Content.expiration_date.is_(None), Content.expiration_date > now)
        )
    
    if tags:
        tags_list = [tag.strip() for tag in tags.split(',')]      
        query = (
            query
            .join(TagAssociation, TagAssociation.entity_id==Content.id)
            .join(Tag, Tag.id == TagAssociation.tag_id)
            .filter(Tag.name.in_(tags_list))
        )
        
    count = query.count()    
    contents = query.all()
    
    return paginator.build_paginated_response(
        items=[content.to_dict() for content in contents],
        endpoint='/contents',
        page=page,
        size=per_page,
        total=count,
    )


@content_router.get("/{id}", status_code=200, response_model=success_response)
async def get_content_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a content by ID or unique_id in case ID fails."""

    content = Content.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=content.organization_id
    )
    
    return success_response(
        message=f"Fetched content successfully",
        status_code=200,
        data=content.to_dict()
    )


@content_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_content(
    id: str,
    organization_id: str,
    payload: content_schemas.ContentUpdate = Form(media_type='multipart/form-data'),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a content"""
    
    previous_content = Content.fetch_by_id(db, id)
    
    user: User = entity.entity
    
    # generate uuid id because of file upload
    model_id = uuid4().hex
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='content:update',
        organization_id=organization_id
    )
    
    if payload.review_status and payload.review_status != 'pending':
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='content:approve',
            organization_id=organization_id
        )
    
    if payload.content_status and payload.content_status == 'published':
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='content:publish',
            organization_id=organization_id
        )
    
    if (payload.content_status and payload.content_status == 'scheduled') or payload.publish_date or payload.expiration_date:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='content:schedule',
            organization_id=organization_id
        )
        
    # if payload.publish_date > payload.expiration_date:
    #     raise HTTPException(400, 'Start date cannot be greater than end date')
        
    if payload.cover_image:
        file = await FileService.upload_file(
            db=db,
            payload=FileBase(
                file=payload.cover_image,
                organization_id=organization_id,
                model_name='contents',
                model_id=model_id,
            ),
            allowed_extensions=['jpg', 'png', 'jpeg'],
            add_to_db=False
        )
        payload.cover_image_url = file['url']
    
    if payload.attachments:
        # TODO: bulk upload files. use celery for this
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=organization_id,
            model_name='contents',
            model_id=model_id,
        )
    
    if payload.content_template_id:
        template = ContentTemplate.fetch_by_id(db, payload.content_template_id)
        payload.content_type = template.content_type
    
    if not payload.cover_image_url:
        payload.cover_image_url = helpers.generate_logo_url(payload.title)
        
    # if payload.additional_info:
    #     payload.additional_info = helpers.format_additional_info_update(json.loads(payload.additional_info))
    #     print(payload.additional_info)
    
    if payload.visibility:    
        payload.visibility = payload.visibility.value
        
    if payload.content_status:    
        payload.content_status = payload.content_status.value
    
    if payload.review_status:    
        payload.review_status = payload.review_status.value
    
    if payload.content_type:
        payload.content_type = payload.content_type if isinstance(payload.content_type, str) else payload.content_type.value
        
    # Create new content version
    ContentVersion.create(
        db=db,
        author_id=user.id,
        content_id=previous_content.id,
        content_template_id=previous_content.content_template_id,
        version=previous_content.current_version,
        title=previous_content.title,
        body=previous_content.body,
        content_type=previous_content.content_type,
        is_visible_on_website=previous_content.is_visible_on_website,
        visibility=previous_content.visibility,
        cover_image_url=previous_content.cover_image_url,
    )

    # Check if body or title were updated
    if (payload.title != previous_content.title) or (payload.body != previous_content.body):
        generate_content_translations.delay(content={
            'id': previous_content.id,
            'title': payload.title,
            'body': payload.body,
        })
    
    content = Content.update(
        db=db,
        id=id,
        current_version=previous_content.current_version + 1,
        **payload.model_dump(exclude_unset=True, exclude=['cover_image', 'attachments', 'tag_ids'])
    )
    
    if payload.tag_ids:
        tag_ids = payload.tag_ids.split(',')
            
        TagService.create_tag_association(
            db=db,
            tag_ids=tag_ids,
            organization_id=organization_id,
            model_type='contents',
            entity_id=content.id
        )

    logger.info(f'Content {content.title} updated')
    
    return success_response(
        message=f"Content updated successfully",
        status_code=200,
        data=content.to_dict()
    )


@content_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_content(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a content"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='content:delete',
        organization_id=organization_id
    )

    Content.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )


# ====================== VERSIONING ==========================

@content_router.get("/{id}/versions", status_code=200)
async def get_content_versions(
    id: str,
    organization_id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all content versions"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, versions, count = ContentVersion.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        organization_id=organization_id,
        content_id=id,
    )
    
    return paginator.build_paginated_response(
        items=[version.to_dict() for version in versions],
        endpoint=f'/contents/{id}/versions',
        page=page,
        size=per_page,
        total=count,
    )


@content_router.get("/versions/{id}", status_code=200, response_model=success_response)
async def get_content_version_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a content version by ID or unique_id in case ID fails."""

    content_version = ContentVersion.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=content_version.content.organization_id
    )
    
    return success_response(
        message=f"Fetched content_version successfully",
        status_code=200,
        data=content_version.to_dict()
    )
    

@content_router.get("/versions/{id}/rollback", status_code=200, response_model=success_response)
async def rollback_to_content_version(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to rolback to a content version."""

    content_version = ContentVersion.fetch_by_id(db, id)
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='content:rollback-version',
        organization_id=content_version.content.organization_id
    )
    
    content = Content.update(
        db=db,
        id=content_version.content_id,
        title=content_version.title,
        body=content_version.body,
        content_type=content_version.content_type,
        is_visible_on_website=content_version.is_visible_on_website,
        visibility=content_version.visibility,
        cover_image_url=content_version.cover_image_url,
        content_template_id=content_version.content_template_id,
        current_version=content_version.version
    )
    
    logger.info(f'Content {content.title} rolled back to version {content.current_version}')
    
    return success_response(
        message=f"Rollback to content version {content_version.version} successful",
        status_code=200,
        data=content.to_dict()
    )


# ================== CONTENT TRANSLATIONS ===================

@content_router.get("/{id}/translations", status_code=200)
async def get_content_translations(
    id: str,
    organization_id: str,
    language_code: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all content translations"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, translations, count = ContentTranslation.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        organization_id=organization_id,
        content_id=id,
        language_code=language_code
    )
    
    return paginator.build_paginated_response(
        items=[translation.to_dict() for translation in translations],
        endpoint=f'/contents/{id}/translations',
        page=page,
        size=per_page,
        total=count,
    )