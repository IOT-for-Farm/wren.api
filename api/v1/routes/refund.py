from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.payment import Payment
from api.v1.models.user import User
from api.v1.models.refund import Refund
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.refund import RefundService
from api.v1.schemas import refund as refund_schemas
from api.utils.loggers import create_logger


refund_router = APIRouter(prefix='/refunds', tags=['Refund'])
logger = create_logger(__name__)

@refund_router.post("", status_code=201, response_model=success_response)
async def create_refund(
    payload: refund_schemas.RefundBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new refund"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='refund:create',
        organization_id=payload.organization_id
    )
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )

    # Get payment
    payment = Payment.fetch_by_id(db, payload.payment_id)
    
    # Calcuate total refunds from payment
    total_refunds = sum([refund.amount for refund in payment.refunds if refund.status =="successful"]) if payment.refunds else 0.00
    logger.info(f'Total refunds: {total_refunds}')
    
    # Get the total amount remaining to be refunded
    refund_amount_remaining = payment.amount - total_refunds
    logger.info(f'Refund amount remaining: {refund_amount_remaining}')
    
    if total_refunds == payment.amount:
        raise HTTPException(400, 'Paymennt refund has been completed')
    
    # Check if amount requested for is greater than the amount left to be refunded
    if payload.amount > float(refund_amount_remaining):
        raise HTTPException(400, 'Amount requested for is higher than the amount in payment')
    
    refund = Refund.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Refund created successfully",
        status_code=201,
        data=refund.to_dict()
    )


@refund_router.get("", status_code=200)
async def get_refunds(
    organization_id: str,
    unique_id: str = None,
    payment_id: str = None,
    status: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all refunds"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, refunds, count = Refund.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        payment_id=payment_id,
        status=status,
    )
    
    return paginator.build_paginated_response(
        items=[refund.to_dict() for refund in refunds],
        endpoint='/refunds',
        page=page,
        size=per_page,
        total=count,
    )


@refund_router.get("/{id}", status_code=200, response_model=success_response)
async def get_refund_by_id(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a refund by ID or unique_id in case ID fails."""

    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )
    
    refund = Refund.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched refund successfully",
        status_code=200,
        data=refund.to_dict()
    )


@refund_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_refund(
    id: str,
    organization_id: str,
    payload: refund_schemas.UpdateRefund,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a refund"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='refund:update',
        organization_id=organization_id
    )
    
    if payload.status == refund_schemas.RefundStatus.pending:
        raise HTTPException(400, 'Cannot update a refund to pending status')
    
    refund = Refund.fetch_by_id(db, id)
    
    if refund.status in ['declined', 'successful']:
        raise HTTPException(400, f'Cannot update a {refund.status} refund')

    refund = Refund.update(
        db=db,
        id=id,
        refund_date=datetime.now() if payload.status == 'successful' else None,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Refund updated successfully",
        status_code=200,
        data=refund.to_dict()
    )


@refund_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_refund(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a refund"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='refund:delete',
        organization_id=organization_id
    )
    
    refund = Refund.fetch_by_id(db, id)
    
    if refund.status in ['pending', 'processing', 'successful']:
        raise HTTPException(400, f'Cannot delete a refund in {refund.status} state')

    Refund.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

