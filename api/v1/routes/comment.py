from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.comment import Comment
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.comment import CommentService
from api.v1.schemas import comment as comment_schemas
from api.utils.loggers import create_logger


comment_router = APIRouter(prefix='/comments', tags=['Comment'])
logger = create_logger(__name__)

@comment_router.post("", status_code=201, response_model=success_response)
async def create_comment(
    organization_id: str,
    payload: comment_schemas.CommentBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new comment"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    user: User = entity.entity
    comment = Comment.create(
        db=db,
        commenter_id=user.id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Comment created successfully",
        status_code=201,
        data=comment.to_dict()
    )


@comment_router.get("", status_code=200)
async def get_comments(
    organization_id: str,
    model_name: str = None,
    model_id: str = None,
    parent_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get comments"""
    
    # AuthService.belongs_to_organization(
    #     entity=entity,
    #     organization_id=organization_id,
    #     db=db
    # )

    query, comments, count = Comment.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        model_name=model_name,
        model_id=model_id,
        parent_id=parent_id,
    )
    
    return paginator.build_paginated_response(
        items=[comment.to_dict() for comment in comments],
        endpoint='/comments',
        page=page,
        size=per_page,
        total=count,
    )


@comment_router.get("/{id}", status_code=200, response_model=success_response)
async def get_comment_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a comment by ID or unique_id in case ID fails."""

    comment = Comment.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched comment successfully",
        status_code=200,
        data=comment.to_dict()
    )


@comment_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_comment(
    id: str,
    payload: comment_schemas.UpdateComment,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a comment"""
    
    user: User = entity.entity
    comment = Comment.fetch_by_id(db, id)
    
    helpers.check_user_is_owner(user_id=user.id, model_instance=comment, user_fk_name='commenter_id')

    updated_comment = Comment.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Comment updated successfully",
        status_code=200,
        data=updated_comment.to_dict()
    )


@comment_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_comment(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a comment"""
    
    user: User = entity.entity
    comment = Comment.fetch_by_id(db, id)
    
    helpers.check_user_is_owner(user_id=user.id, model_instance=comment, user_fk_name='commenter_id')

    Comment.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
    )

