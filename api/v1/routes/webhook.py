from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.webhook import Webhook
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.webhook import WebhookService
from api.v1.schemas import webhook as webhook_schemas
from api.utils.loggers import create_logger


webhook_router = APIRouter(prefix='/webhooks', tags=['Webhook'])
logger = create_logger(__name__)

@webhook_router.post("", status_code=201, response_model=success_response)
async def create_webhook(
    payload: webhook_schemas.WebhookBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new webhook"""

    webhook = Webhook.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Webhook with id {webhook.id} created')

    return success_response(
        message=f"Webhook created successfully",
        status_code=201,
        data=webhook.to_dict()
    )


@webhook_router.get("", status_code=200)
async def get_webhooks(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all webhooks"""

    query, webhooks, count = Webhook.fetch_by_field(
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
        items=[webhook.to_dict() for webhook in webhooks],
        endpoint='/webhooks',
        page=page,
        size=per_page,
        total=count,
    )


@webhook_router.get("/{id}", status_code=200, response_model=success_response)
async def get_webhook_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a webhook by ID or unique_id in case ID fails."""

    webhook = Webhook.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched webhook successfully",
        status_code=200,
        data=webhook.to_dict()
    )


@webhook_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_webhook(
    id: str,
    payload: webhook_schemas.UpdateWebhook,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a webhook"""

    webhook = Webhook.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Webhook with id {webhook.id} updated')

    return success_response(
        message=f"Webhook updated successfully",
        status_code=200,
        data=webhook.to_dict()
    )


@webhook_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_webhook(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a webhook"""

    Webhook.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

