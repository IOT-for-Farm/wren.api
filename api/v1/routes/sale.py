from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.sale import Sale
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.sale import SaleService
from api.v1.schemas import sale as sale_schemas
from api.utils.loggers import create_logger


sale_router = APIRouter(prefix='/sales', tags=['Sale'])
logger = create_logger(__name__)

@sale_router.post("", status_code=201, response_model=success_response)
async def create_sale(
    payload: sale_schemas.SaleBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new sale"""

    sale = Sale.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Sale created successfully",
        status_code=200,
        data=sale.to_dict()
    )


@sale_router.get("", status_code=200)
async def get_sales(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all sales"""

    query, sales, count = Sale.all(
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
        items=[sale.to_dict() for sale in sales],
        endpoint='/sales',
        page=page,
        size=per_page,
        total=count,
    )


@sale_router.get("/{id}", status_code=200, response_model=success_response)
async def get_sale_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a sale by ID or unique_id in case ID fails."""

    sale = Sale.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched sale successfully",
        status_code=200,
        data=sale.to_dict()
    )


@sale_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_sale(
    id: str,
    payload: sale_schemas.UpdateSale,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a sale"""

    sale = Sale.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Sale updated successfully",
        status_code=200,
        data=sale.to_dict()
    )


@sale_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_sale(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a sale"""

    Sale.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

