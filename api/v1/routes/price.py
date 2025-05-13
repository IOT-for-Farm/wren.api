from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.product import ProductPrice, Product
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.price import PriceService
from api.v1.schemas import price as price_schemas
from api.utils.loggers import create_logger


price_router = APIRouter(prefix='/prices', tags=['Price'])
logger = create_logger(__name__)

@price_router.post("", status_code=201, response_model=success_response)
async def create_price(
    organization_id: str,
    payload: price_schemas.PriceCreate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new price"""
        
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='price:create',
        organization_id=organization_id
    )
    
    # Deactiveate all active product prices so as to have only one active price per product
    if payload.is_active == True:
        PriceService.deactivate_active_prices(db, payload.product_id, payload.variant_id)

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
    organization_id: str,
    product_id: str,
    variant_id: str = None,
    is_active: bool = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all prices"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, prices, count = ProductPrice.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        organization_id=organization_id,
        product_id=product_id,
        variant_id=variant_id,
        is_active=is_active,
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
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a price by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    price = ProductPrice.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched price successfully",
        status_code=200,
        data=price.to_dict()
    )


@price_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_price(
    id: str,
    product_id: str,
    organization_id: str,
    payload: price_schemas.PriceUpdate,
    variant_id: Optional[str] = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a price"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='price:update',
        organization_id=organization_id
    )

    # Deactiveate all active product prices so as to have only one active price per product
    if payload.is_active and payload.is_active == True:
        PriceService.deactivate_active_prices(db, product_id, variant_id)
        
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
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a price"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='price:delete',
        organization_id=organization_id
    )

    ProductPrice.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

