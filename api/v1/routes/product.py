from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.product import Product
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.product import ProductService
from api.v1.schemas import product as product_schemas
from api.utils.loggers import create_logger


product_router = APIRouter(prefix='/products', tags=['Product'])
logger = create_logger(__name__)

@product_router.post("", status_code=201, response_model=success_response)
async def create_product(
    payload: product_schemas.ProductBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new product"""

    product = Product.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Product created successfully",
        status_code=200,
        data=product.to_dict()
    )


@product_router.get("", status_code=200)
async def get_products(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all products"""

    query, products, count = Product.all(
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
        items=[product.to_dict() for product in products],
        endpoint='/products',
        page=page,
        size=per_page,
        total=count,
    )


@product_router.get("/{id}", status_code=200, response_model=success_response)
async def get_product_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a product by ID or unique_id in case ID fails."""

    product = Product.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched product successfully",
        status_code=200,
        data=product.to_dict()
    )


@product_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_product(
    id: str,
    payload: product_schemas.UpdateProduct,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a product"""

    product = Product.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Product updated successfully",
        status_code=200,
        data=product.to_dict()
    )


@product_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_product(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a product"""

    Product.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

