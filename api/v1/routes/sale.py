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
from api.v1.services.tag import TagService


sale_router = APIRouter(prefix='/sales', tags=['Sale'])
logger = create_logger(__name__)

@sale_router.post("", status_code=201, response_model=success_response)
async def create_sale(
    payload: sale_schemas.SaleCreate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new sale"""
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )

    sale = Sale.create(
        db=db,
        **payload.model_dump(exclude_unset=True, exclude=['tag_ids'])
    )
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=payload.organization_id,
            model_type='sales',
            entity_id=sale.id
        )

    logger.info(f'Sale with {sale.id} created')
    
    return success_response(
        message=f"Sale created successfully",
        status_code=200,
        data=sale.to_dict()
    )


@sale_router.get("", status_code=200)
async def get_sales(
    organization_id: str,
    product_id: str = None,
    vendor_id: str = None,
    customer_id: str = None,
    unique_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all sales"""

    query, sales, count = Sale.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        product_id=product_id,
        customer_id=customer_id,
        vendor_id=vendor_id
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
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
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
    organization_id: str,
    payload: sale_schemas.UpdateSale,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a sale"""

    sale = Sale.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['tag_ids'])
    )
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=organization_id,
            model_type='sales',
            entity_id=sale.id
        )

    logger.info(f'Sale with {sale.id} updated')

    return success_response(
        message=f"Sale updated successfully",
        status_code=200,
        data=sale.to_dict()
    )


@sale_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_sale(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a sale"""

    Sale.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

