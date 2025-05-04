from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
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
    payload: inventory_schemas.InventoryBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new inventory"""

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
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all inventory"""

    query, inventory, count = Inventory.all(
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
        items=[inventory.to_dict() for inventory in inventory],
        endpoint='/inventory',
        page=page,
        size=per_page,
        total=count,
    )


@inventory_router.get("/{id}", status_code=200, response_model=success_response)
async def get_inventory_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a inventory by ID or unique_id in case ID fails."""

    inventory = Inventory.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched inventory successfully",
        status_code=200,
        data=inventory.to_dict()
    )


@inventory_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_inventory(
    id: str,
    payload: inventory_schemas.UpdateInventory,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a inventory"""

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
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a inventory"""

    Inventory.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

