from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.product import ProductPrice
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.price import PriceService
from api.v1.schemas import price as price_schemas
from api.utils.loggers import create_logger


price_router = APIRouter(prefix='/prices', tags=['Price'])
logger = create_logger(__name__)

@price_router.post("", status_code=201, response_model=success_response)
async def create_price(
    payload: price_schemas.PriceBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new price"""

    price = ProductPrice.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Price created successfully",
        status_code=200,
        data=price.to_dict()
    )


@price_router.get("", status_code=200)
async def get_prices(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all prices"""

    query, prices, count = ProductPrice.all(
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
        items=[price.to_dict() for price in prices],
        endpoint='/prices',
        page=page,
        size=per_page,
        total=count,
    )


@price_router.get("/{id}", status_code=200, response_model=success_response)
async def get_price_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a price by ID or unique_id in case ID fails."""

    price = ProductPrice.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched price successfully",
        status_code=200,
        data=price.to_dict()
    )


@price_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_price(
    id: str,
    payload: price_schemas.UpdatePrice,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a price"""

    price = ProductPrice.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Price updated successfully",
        status_code=200,
        data=price.to_dict()
    )


@price_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_price(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a price"""

    ProductPrice.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

