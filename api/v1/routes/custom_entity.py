from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.custom_entity import Custom_entity
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.custom_entity import Custom_entityService
from api.v1.schemas import custom_entity as custom_entity_schemas
from api.utils.loggers import create_logger


custom_entity_router = APIRouter(prefix='/custom_entitys', tags=['Custom_entity'])
logger = create_logger(__name__)

@custom_entity_router.post("", status_code=201, response_model=success_response)
async def create_custom_entity(
    payload: custom_entity_schemas.Custom_entityBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new custom_entity"""

    custom_entity = Custom_entity.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Custom_entity with id {custom_entity.id} created')

    return success_response(
        message=f"Custom_entity created successfully",
        status_code=201,
        data=custom_entity.to_dict()
    )


@custom_entity_router.get("", status_code=200)
async def get_custom_entitys(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all custom_entitys"""

    query, custom_entitys, count = Custom_entity.fetch_by_field(
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
        items=[custom_entity.to_dict() for custom_entity in custom_entitys],
        endpoint='/custom_entitys',
        page=page,
        size=per_page,
        total=count,
    )


@custom_entity_router.get("/{id}", status_code=200, response_model=success_response)
async def get_custom_entity_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a custom_entity by ID or unique_id in case ID fails."""

    custom_entity = Custom_entity.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched custom_entity successfully",
        status_code=200,
        data=custom_entity.to_dict()
    )


@custom_entity_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_custom_entity(
    id: str,
    payload: custom_entity_schemas.UpdateCustom_entity,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a custom_entity"""

    custom_entity = Custom_entity.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Custom_entity with id {custom_entity.id} updated')

    return success_response(
        message=f"Custom_entity updated successfully",
        status_code=200,
        data=custom_entity.to_dict()
    )


@custom_entity_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_custom_entity(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a custom_entity"""

    Custom_entity.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

