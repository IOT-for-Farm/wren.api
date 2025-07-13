from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.tag import Tag
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.auth import AuthService
from api.v1.services.tag import TagService
from api.v1.schemas import tag as tag_schemas
from api.utils.loggers import create_logger


tag_router = APIRouter(prefix='/tags', tags=['Tag'])
logger = create_logger(__name__)

@tag_router.post("", status_code=201, response_model=success_response)
async def create_tag(
    payload: tag_schemas.TagBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new tag"""
    
    AuthService.belongs_to_organization(
        db=db,
        organization_id=payload.organization_id,
        entity=entity
    )        

    payload.name = payload.name.lower()
    payload.model_type = payload.model_type.lower()
    
    existing_tag = Tag.fetch_one_by_field(
        db=db,
        throw_error=False,
        name=payload.name,
        organization_id=payload.organization_id,
        model_type=payload.model_type
    )
    
    if existing_tag:
        raise HTTPException(400, detail="Tag already exists")
    
    if payload.parent_id:
        parent_tag = Tag.fetch_by_id(db, payload.parent_id)
        if payload.organization_id != parent_tag.organization_id:
            raise HTTPException(400, detail="Parent tag does not belong to the organization")
        
        if payload.parent_id == existing_tag.id:
            raise HTTPException(400, detail="Tag cannot be its own parent")
        
    tag = Tag.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Tag created successfully",
        status_code=200,
        data=tag.to_dict()
    )


@tag_router.get("", status_code=200)
async def get_tags(
    organization_id: str,
    name: str = None,
    group: str = None,
    model_type: str = None,
    parent_id: str = None,
    page: int = 1,
    per_page: int = 25,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all tags"""
    
    AuthService.belongs_to_organization(
        db=db,
        organization_id=organization_id,
        entity=entity
    )  

    query, tags, count = Tag.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        organization_id=organization_id,
        group=group,
        model_type=model_type,
        parent_id=parent_id,
    )
    
    return paginator.build_paginated_response(
        items=[tag.to_dict() for tag in tags],
        endpoint='/tags',
        page=page,
        size=per_page,
        total=count,
    )
    

@tag_router.post("/attach", status_code=201, response_model=success_response)
async def attach_tag_to_eneity(
    organization_id: str,
    payload: tag_schemas.AttachOrDetatchTag,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to attach a tag to an entity"""
    
    AuthService.belongs_to_organization(
        db=db,
        organization_id=organization_id,
        entity=entity
    )  
    
    TagService.create_tag_association(
        db=db,
        tag_ids=payload.tag_ids,
        organization_id=organization_id,
        model_type=payload.model_type,
        entity_id=payload.entity_id
    )

    return success_response(
        message=f"Tag(s) attached to entity successfully",
        status_code=200
    )
    

@tag_router.post("/detatch", status_code=201, response_model=success_response)
async def detatch_tag_from_entity(
    organization_id: str,
    payload: tag_schemas.AttachOrDetatchTag,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to detatch a tag from an entity"""
    
    AuthService.belongs_to_organization(
        db=db,
        organization_id=organization_id,
        entity=entity
    )  
    
    TagService.delete_tag_association(
        db=db,
        tag_ids=payload.tag_ids,
        organization_id=organization_id,
        model_type=payload.model_type,
        entity_id=payload.entity_id
    )

    return success_response(
        message=f"Tag(s) detatched from entity successfully",
        status_code=200
    )


@tag_router.get("/{id}", status_code=200, response_model=success_response)
async def get_tag_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a tag by ID or unique_id in case ID fails."""

    tag = Tag.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        db=db,
        organization_id=tag.organization_id,
        entity=entity
    )  
    
    return success_response(
        message=f"Fetched tag successfully",
        status_code=200,
        data=tag.to_dict()
    )


@tag_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_tag(
    id: str,
    organization_id: str,
    payload: tag_schemas.UpdateTag,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a tag"""

    AuthService.belongs_to_organization(
        db=db,
        organization_id=organization_id,
        entity=entity
    )
    
    tag = Tag.fetch_by_id(db, id)
    
    if organization_id != tag.organization_id:
        raise HTTPException(400, detail="Tag does not belong to the organization")
    
    if payload.parent_id:
        parent_tag = Tag.fetch_by_id(db, payload.parent_id)
        if organization_id != parent_tag.organization_id:
            raise HTTPException(400, detail="Parent tag does not belong to the organization")
        
        if payload.parent_id == tag.id:
            raise HTTPException(400, detail="Tag cannot be its own parent")
    
    if payload.name:
        existing_tag = Tag.fetch_one_by_field(
            db=db,
            throw_error=False,
            name=payload.name,
            organization_id=organization_id,
            model_type=tag.model_type
        )
        
        if existing_tag and existing_tag.id != id:
            raise HTTPException(400, detail="Tag with this name already exists")
        
        payload.name = payload.name.lower()
    
    if payload.model_type:
        payload.model_type = payload.model_type.lower()
        
    updated_tag = Tag.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Tag updated successfully",
        status_code=200,
        data=updated_tag.to_dict()
    )


@tag_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_tag(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a tag"""
    
    AuthService.belongs_to_organization(
        db=db,
        organization_id=organization_id,
        entity=entity
    )

    Tag.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

