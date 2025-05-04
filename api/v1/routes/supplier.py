from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.supplier import Supplier
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.supplier import SupplierService
from api.v1.schemas import supplier as supplier_schemas
from api.utils.loggers import create_logger


supplier_router = APIRouter(prefix='/suppliers', tags=['Supplier'])
logger = create_logger(__name__)

@supplier_router.post("", status_code=201, response_model=success_response)
async def create_supplier(
    payload: supplier_schemas.SupplierBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new supplier"""

    supplier = Supplier.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Supplier created successfully",
        status_code=200,
        data=supplier.to_dict()
    )


@supplier_router.get("", status_code=200)
async def get_suppliers(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all suppliers"""

    query, suppliers, count = Supplier.all(
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
        items=[supplier.to_dict() for supplier in suppliers],
        endpoint='/suppliers',
        page=page,
        size=per_page,
        total=count,
    )


@supplier_router.get("/{id}", status_code=200, response_model=success_response)
async def get_supplier_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a supplier by ID or unique_id in case ID fails."""

    supplier = Supplier.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched supplier successfully",
        status_code=200,
        data=supplier.to_dict()
    )


@supplier_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_supplier(
    id: str,
    payload: supplier_schemas.UpdateSupplier,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a supplier"""

    supplier = Supplier.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Supplier updated successfully",
        status_code=200,
        data=supplier.to_dict()
    )


@supplier_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_supplier(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a supplier"""

    Supplier.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

