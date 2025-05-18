from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.receipt import Receipt
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.receipt import ReceiptService
from api.v1.schemas import receipt as receipt_schemas
from api.utils.loggers import create_logger


receipt_router = APIRouter(prefix='/receipts', tags=['Receipt'])
logger = create_logger(__name__)

@receipt_router.post("", status_code=201, response_model=success_response)
async def create_receipt(
    payload: receipt_schemas.GenerateReceipt,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new receipt"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='receipt:create',
        organization_id=payload.organization_id
    )

    receipt = ReceiptService.generate_receipt(
        db=db,
        organization_id=payload.organization_id,
        invoice_id=payload.invoice_id,
        unique_id=payload.unique_id,
        send_notification=payload.send_notification,
        template_id=payload.template_id,
        context=payload.context,
        transaction_reference=payload.transaction_reference,
    )

    logger.info(f'Receipt with id {receipt.id} created')

    return success_response(
        message=f"Receipt created successfully",
        status_code=201,
        # data=receipt.to_dict()
    )


@receipt_router.get("", status_code=200)
async def get_receipts(
    organization_id: str,
    unique_id: str = None,
    customer_id: str = None,
    order_id: str = None,
    vendor_id: str = None,
    invoice_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all receipts"""

    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )
    
    query, receipts, count = Receipt.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        customer_id=customer_id,
        vendor_id=vendor_id,
        order_id=order_id,
        invoice_id=invoice_id,
    )
    
    return paginator.build_paginated_response(
        items=[receipt.to_dict() for receipt in receipts],
        endpoint='/receipts',
        page=page,
        size=per_page,
        total=count,
    )


@receipt_router.get("/{id}", status_code=200, response_model=success_response)
async def get_receipt_by_id(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a receipt by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    receipt = Receipt.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched receipt successfully",
        status_code=200,
        data=receipt.to_dict()
    )


@receipt_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_receipt(
    id: str,
    organization_id: str,
    payload: receipt_schemas.UpdateReceipt,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a receipt"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='receipt:update',
        organization_id=organization_id
    )

    receipt = Receipt.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Receipt with id {receipt.id} updated')

    return success_response(
        message=f"Receipt updated successfully",
        status_code=200,
        data=receipt.to_dict()
    )


@receipt_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_receipt(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a receipt"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='receipt:delete',
        organization_id=organization_id
    )

    Receipt.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

