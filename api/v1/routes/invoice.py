from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import and_
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
    payload: invoice_schemas.GenerateInvoice,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new invoice"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='invoice:create',
        organization_id=payload.organization_id
    )
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )
        
    if not payload.due_date:
        # Set due date to be 14 days later
        payload.due_date = datetime.now() + timedelta(days=14)        

    if payload.order_id:
        invoice = InvoiceService.generate_order_invoice(
            db=db,
            unique_id=payload.unique_id,
            organization_id=payload.organization_id,
            order_id=payload.order_id,
            due_date=payload.due_date,
            currency_code=payload.currency_code,
            send_notification=payload.send_notification,
            template_id=payload.template_id,
            context=payload.context,
            recipients=payload.recipients,
        )
    
    elif payload.vendor_id:
        invoice = InvoiceService.generate_vendor_invoice(
            db=db,
            organization_id=payload.organization_id,
            unique_id=payload.unique_id,
            vendor_id=payload.vendor_id,
            due_date=payload.due_date,
            year_to_generate_for=payload.year,
            month_to_generate_for=payload.month,
            currency_code=payload.currency_code,
            send_notification=payload.send_notification,
            template_id=payload.template_id,
            context=payload.context,
            recipients=payload.recipients,
        )
    
    else:
        invoice = InvoiceService.generate_custom_invoice(
            db=db,
            organization_id=payload.organization_id,
            unique_id=payload.unique_id,
            due_date=payload.due_date,
            currency_code=payload.currency_code,
            send_notification=payload.send_notification,
            template_id=payload.template_id,
            context=payload.context,
            recipients=payload.recipients,
            items=payload.items,
            customer_id=payload.customer_id
        )
        
        
    # TODO: Generate department invoice
    
    # if payload.department_id:
    #     pass

    return success_response(
        message=f"Invoice created successfully",
        status_code=201,
        data=invoice.to_dict()
    )


@invoice_router.get("", status_code=200)
async def get_invoices(
    organization_id: str,
    unique_id: str = None,
    department_id: str = None,
    order_id: str = None,
    customer_id: str = None,
    vendor_id: str = None,
    status: str = None,
    issue_date: datetime = None,
    due_date: datetime =None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all invoices"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, invoices, count = Invoice.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        department_id=department_id,
        order_id=order_id,
        customer_id=customer_id,
        vendor_id=vendor_id,
        status=status
    )
    
    if issue_date and not due_date:
        query = query.filter(Invoice.issue_date >= issue_date)
    
    if due_date and not issue_date:
        query = query.filter(Invoice.due_date >= due_date)
        
    if issue_date and due_date:
        query = query.filter(
            and_(
                Invoice.due_date <= due_date,
                Invoice.issue_date >= issue_date,
            )
        )
        
    invoices, count = paginator.paginate_query(query, page, per_page)
    
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
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a invoice by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    invoice = Invoice.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched invoice successfully",
        status_code=200,
        data=invoice.to_dict()
    )


@invoice_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_invoice(
    id: str,
    organization_id: str,
    payload: invoice_schemas.UpdateInvoice,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a invoice"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='invoice:update',
        organization_id=organization_id
    )
    
    if payload.items:
        invoice_items = []
        for item in payload.items:
            invoice_items.append({
                "rate": item.rate,
                "quantity": item.quantity,
                "description": item.description,
            })
            
        payload.items = invoice_items

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
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a invoice"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='invoice:delete',
        organization_id=organization_id
    )

    Invoice.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

