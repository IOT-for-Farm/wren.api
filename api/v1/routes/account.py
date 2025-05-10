from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.account import Account
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.account import AccountService
from api.v1.schemas import account as account_schemas
from api.utils.loggers import create_logger


account_router = APIRouter(prefix='/accounts', tags=['Account'])
logger = create_logger(__name__)

@account_router.post("", status_code=201, response_model=success_response)
async def create_account(
    payload: account_schemas.AccountBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new account"""

    account = Account.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Account created successfully",
        status_code=201,
        data=account.to_dict()
    )


@account_router.get("", status_code=200)
async def get_accounts(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all accounts"""

    query, accounts, count = Account.all(
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
        items=[account.to_dict() for account in accounts],
        endpoint='/accounts',
        page=page,
        size=per_page,
        total=count,
    )


@account_router.get("/{id}", status_code=200, response_model=success_response)
async def get_account_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a account by ID or unique_id in case ID fails."""

    account = Account.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched account successfully",
        status_code=200,
        data=account.to_dict()
    )


@account_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_account(
    id: str,
    payload: account_schemas.UpdateAccount,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a account"""

    account = Account.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Account updated successfully",
        status_code=200,
        data=account.to_dict()
    )


@account_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_account(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a account"""

    Account.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

