from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.product import ProductPrice
from api.v1.models.user import User
from api.v1.models.inventory import Inventory
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.inventory import InventoryService
from api.v1.schemas import inventory as inventory_schemas
from api.utils.loggers import create_logger


inventory_router = APIRouter(prefix='/inventory', tags=['Inventory'])
logger = create_logger(__name__)

@inventory_router.post("", status_code=201, response_model=success_response)
async def create_inventory(
    organization_id: str,
    payload: inventory_schemas.InventoryBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new inventory"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='inventory:create',
        organization_id=organization_id
    )
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=organization_id,
        )
    
    inventory = Inventory.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Inventory created successfully",
        status_code=200,
        data=inventory.to_dict()
    )


@inventory_router.get("", status_code=200)
async def get_inventory(
    organization_id: str,
    product_id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all inventory"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, inventory, count = Inventory.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        product_id=product_id
    )
    
    return paginator.build_paginated_response(
        items=[inventory.to_dict() for inventory in inventory],
        endpoint='/inventory',
        page=page,
        size=per_page,
        total=count,
    )


@inventory_router.get("/{id}", status_code=200, response_model=success_response)
async def get_inventory_by_id(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a inventory by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    inventory = Inventory.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched inventory successfully",
        status_code=200,
        data=inventory.to_dict()
    )


@inventory_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_inventory(
    id: str,
    organization_id: str,
    payload: inventory_schemas.UpdateInventory,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a inventory"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='inventory:update',
        organization_id=organization_id
    )

    inventory = Inventory.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Inventory updated successfully",
        status_code=200,
        data=inventory.to_dict()
    )


@inventory_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_inventory(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a inventory"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='inventory:delete',
        organization_id=organization_id
    )

    Inventory.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

