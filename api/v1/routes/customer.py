from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.business_partner import BusinessPartner
from api.v1.models.user import User
from api.v1.models.customer import Customer
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.customer import CustomerService
from api.v1.schemas import customer as customer_schemas
from api.utils.loggers import create_logger


customer_router = APIRouter(prefix='/customers', tags=['Customer'])
logger = create_logger(__name__)

@customer_router.post("", status_code=201, response_model=success_response)
async def create_customer(
    business_partner_id: str,
    organization_id: str,
    payload: customer_schemas.CustomerBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new customer"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='customer:create',
        organization_id=organization_id
    )
    
    # Check if business partner exists
    BusinessPartner.fetch_one_by_field(
        db=db,
        id=business_partner_id,
        partner_type="customer"
    )
    
    # Check for existing customer
    existing_customer = Customer.fetch_one_by_field(
        db=db, throw_error=False,
        business_partner_id=business_partner_id
    )
    
    if existing_customer:
        raise HTTPException(400, "Customer with this business partner id already exists")
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=organization_id,
        )

    customer = Customer.create(
        db=db,
        business_partner_id=business_partner_id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Customer created successfully",
        status_code=200,
        data=customer.to_dict()
    )


@customer_router.get("", status_code=200)
async def get_customers(
    organization_id: str,
    first_name: str = None,
    last_name: str = None,
    customer_type: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all customers"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, customers, count = Customer.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        customer_type=customer_type
    )
    
    query = (
        query
        .join(BusinessPartner, BusinessPartner.id==Customer.business_partner_id)
        .filter(
            BusinessPartner.partner_type=='customer',
            BusinessPartner.organization_id== organization_id
        )
    )

    if first_name:
        query = query.filter(BusinessPartner.first_name.ilike(f"%{first_name}%"))
        
    if last_name:
        query = query.filter(BusinessPartner.last_name.ilike(f"%{last_name}%"))
    
    customers = query.all()
    count = query.count()
    
    return paginator.build_paginated_response(
        items=[customer.to_dict() for customer in customers],
        endpoint='/customers',
        page=page,
        size=per_page,
        total=count,
    )


@customer_router.get("/{id}", status_code=200, response_model=success_response)
async def get_customer_by_id(
    organization_id: str,
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a customer by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    customer = Customer.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched customer successfully",
        status_code=200,
        data=customer.to_dict()
    )


@customer_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_customer(
    organization_id: str,
    id: str,
    payload: customer_schemas.UpdateCustomer,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a customer"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='customer:update',
        organization_id=organization_id
    )

    customer = Customer.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Customer updated successfully",
        status_code=200,
        data=customer.to_dict()
    )


@customer_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_customer(
    organization_id: str,
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a customer"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='customer:delete',
        organization_id=organization_id
    )

    Customer.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

