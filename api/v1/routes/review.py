from fastapi import APIRouter, Depends
import sqlalchemy as sa
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.review import Review
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.review import ReviewService
from api.v1.schemas import review as review_schemas
from api.utils.loggers import create_logger


review_router = APIRouter(prefix='/reviews', tags=['Review'])
logger = create_logger(__name__)

@review_router.post("", status_code=201, response_model=success_response)
async def create_review(
    payload: review_schemas.ReviewBase,
    db: Session=Depends(get_db), 
    # entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new review"""

    review = Review.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Review created successfully",
        status_code=201,
        data=review.to_dict()
    )


@review_router.get("", status_code=200)
async def get_reviews(
    model_name: str = None,
    model_id: str = None,
    star_rating: int = None,
    is_published: bool = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    # entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all reviews"""

    query, reviews, count = Review.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        model_name=model_name,
        model_id=model_id,
        star_rating=star_rating,
        is_published=is_published
    )
    
    return paginator.build_paginated_response(
        items=[review.to_dict() for review in reviews],
        endpoint='/reviews',
        page=page,
        size=per_page,
        total=count,
    )


@review_router.get("/{id}", status_code=200, response_model=success_response)
async def get_review_by_id(
    id: str,
    db: Session=Depends(get_db), 
    # entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a review by ID or unique_id in case ID fails."""

    review = Review.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched review successfully",
        status_code=200,
        data=review.to_dict()
    )


@review_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_review(
    id: str,
    payload: review_schemas.UpdateReview,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a review"""
    
    review = Review.fetch_by_id(db, id)
    
    if payload.is_published and payload.is_published == True:
        payload.published_at = sa.func.now()
    
    updated_review = Review.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Review updated successfully",
        status_code=200,
        data=updated_review.to_dict()
    )


@review_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_review(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a review"""
    
    review = Review.fetch_by_id(db, id)
    
    Review.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

