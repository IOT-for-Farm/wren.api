from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.category import Category
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.category import CategoryService
from api.v1.schemas import category as category_schemas
from api.utils.loggers import create_logger


category_router = APIRouter(prefix='/categories', tags=['Category'])
logger = create_logger(__name__)

@category_router.post("", status_code=201, response_model=success_response)
async def create_category(
    payload: category_schemas.CategoryBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new category"""

    category = Category.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Category created successfully",
        status_code=200,
        data=category.to_dict()
    )


@category_router.get("", status_code=200)
async def get_categories(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all categories"""

    query, categories, count = Category.all(
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
        items=[category.to_dict() for category in categories],
        endpoint='/categories',
        page=page,
        size=per_page,
        total=count,
    )


@category_router.get("/{id}", status_code=200, response_model=success_response)
async def get_category_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a category by ID or unique_id in case ID fails."""

    category = Category.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched category successfully",
        status_code=200,
        data=category.to_dict()
    )


@category_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_category(
    id: str,
    payload: category_schemas.UpdateCategory,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a category"""

    category = Category.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Category updated successfully",
        status_code=200,
        data=category.to_dict()
    )


@category_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_category(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a category"""

    Category.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

