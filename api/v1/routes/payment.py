from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.payment import Payment
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.payment import PaymentService
from api.v1.schemas import payment as payment_schemas
from api.utils.loggers import create_logger


payment_router = APIRouter(prefix='/payments', tags=['Payment'])
logger = create_logger(__name__)

@payment_router.post("", status_code=201, response_model=success_response)
async def create_payment(
    payload: payment_schemas.PaymentBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new payment"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='payment:create',
        organization_id=payload.organization_id
    )
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )

    payment = Payment.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f"payment with id {payment.id} created successfully")
    
    return success_response(
        message=f"Payment created successfully",
        status_code=201,
        data=payment.to_dict()
    )


@payment_router.get("", status_code=200)
async def get_payments(
    organization_id: str,
    unique_id: str = None,
    invoice_id: str = None,
    status: str = None,
    method: str = None,
    payment_date: datetime = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all payments"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, payments, count = Payment.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        status=status,
        method=method,
        invoice_id=invoice_id,
    )
    
    if payment_date:
        query = query.filter(Payment.payment_date >= payment_date)
        payments, count = paginator.paginate_query(query, page, per_page)
    
    return paginator.build_paginated_response(
        items=[payment.to_dict() for payment in payments],
        endpoint='/payments',
        page=page,
        size=per_page,
        total=count,
    )


@payment_router.get("/{id}", status_code=200, response_model=success_response)
async def get_payment_by_id(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a payment by ID or unique_id in case ID fails."""

    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )
    
    payment = Payment.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched payment successfully",
        status_code=200,
        data=payment.to_dict()
    )


@payment_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_payment(
    id: str,
    organization_id: str,
    payload: payment_schemas.UpdatePayment,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a payment"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='payment:update',
        organization_id=organization_id
    )
    
    payment = Payment.fetch_by_id(db, id)
    
    if payment.status in ['failed', 'cancelled']:
        raise HTTPException(400, f'Cannot make update to a {payment.status} payment')

    payment = Payment.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Payment updated successfully",
        status_code=200,
        data=payment.to_dict()
    )


@payment_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_payment(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a payment"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='payment:delete',
        organization_id=organization_id
    )

    Payment.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

