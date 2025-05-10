from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
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
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new refund"""

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
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all refunds"""

    query, refunds, count = Refund.all(
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
        items=[refund.to_dict() for refund in refunds],
        endpoint='/refunds',
        page=page,
        size=per_page,
        total=count,
    )


@refund_router.get("/{id}", status_code=200, response_model=success_response)
async def get_refund_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a refund by ID or unique_id in case ID fails."""

    refund = Refund.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched refund successfully",
        status_code=200,
        data=refund.to_dict()
    )


@refund_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_refund(
    id: str,
    payload: refund_schemas.UpdateRefund,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a refund"""

    refund = Refund.update(
        db=db,
        id=id,
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
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a refund"""

    Refund.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

