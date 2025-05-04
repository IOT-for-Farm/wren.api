from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
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
    payload: customer_schemas.CustomerBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new customer"""

    customer = Customer.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Customer created successfully",
        status_code=200,
        data=customer.to_dict()
    )


@customer_router.get("", status_code=200)
async def get_customers(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all customers"""

    query, customers, count = Customer.all(
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
        items=[customer.to_dict() for customer in customers],
        endpoint='/customers',
        page=page,
        size=per_page,
        total=count,
    )


@customer_router.get("/{id}", status_code=200, response_model=success_response)
async def get_customer_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a customer by ID or unique_id in case ID fails."""

    customer = Customer.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched customer successfully",
        status_code=200,
        data=customer.to_dict()
    )


@customer_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_customer(
    id: str,
    payload: customer_schemas.UpdateCustomer,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a customer"""

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
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a customer"""

    Customer.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

