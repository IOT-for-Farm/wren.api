from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.invoice import Invoice
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.invoice import InvoiceService
from api.v1.schemas import invoice as invoice_schemas
from api.utils.loggers import create_logger


invoice_router = APIRouter(prefix='/invoices', tags=['Invoice'])
logger = create_logger(__name__)

@invoice_router.post("", status_code=201, response_model=success_response)
async def create_invoice(
    payload: invoice_schemas.InvoiceBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new invoice"""

    invoice = Invoice.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Invoice created successfully",
        status_code=201,
        data=invoice.to_dict()
    )


@invoice_router.get("", status_code=200)
async def get_invoices(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all invoices"""

    query, invoices, count = Invoice.all(
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
        items=[invoice.to_dict() for invoice in invoices],
        endpoint='/invoices',
        page=page,
        size=per_page,
        total=count,
    )


@invoice_router.get("/{id}", status_code=200, response_model=success_response)
async def get_invoice_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a invoice by ID or unique_id in case ID fails."""

    invoice = Invoice.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched invoice successfully",
        status_code=200,
        data=invoice.to_dict()
    )


@invoice_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_invoice(
    id: str,
    payload: invoice_schemas.UpdateInvoice,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a invoice"""

    invoice = Invoice.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Invoice updated successfully",
        status_code=200,
        data=invoice.to_dict()
    )


@invoice_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_invoice(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a invoice"""

    Invoice.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

