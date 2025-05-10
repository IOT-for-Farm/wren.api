from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.order import Order
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.order import OrderService
from api.v1.schemas import order as order_schemas
from api.utils.loggers import create_logger


order_router = APIRouter(prefix='/orders', tags=['Order'])
logger = create_logger(__name__)

@order_router.post("", status_code=201, response_model=success_response)
async def create_order(
    payload: order_schemas.OrderBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new order"""

    order = Order.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Order created successfully",
        status_code=201,
        data=order.to_dict()
    )


@order_router.get("", status_code=200)
async def get_orders(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all orders"""

    query, orders, count = Order.all(
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
        items=[order.to_dict() for order in orders],
        endpoint='/orders',
        page=page,
        size=per_page,
        total=count,
    )


@order_router.get("/{id}", status_code=200, response_model=success_response)
async def get_order_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a order by ID or unique_id in case ID fails."""

    order = Order.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched order successfully",
        status_code=200,
        data=order.to_dict()
    )


@order_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_order(
    id: str,
    payload: order_schemas.UpdateOrder,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a order"""

    order = Order.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Order updated successfully",
        status_code=200,
        data=order.to_dict()
    )


@order_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_order(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a order"""

    Order.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

