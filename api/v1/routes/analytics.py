from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.analytics import Analytics
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.analytics import AnalyticsService
from api.v1.schemas import analytics as analytics_schemas
from api.utils.loggers import create_logger


analytics_router = APIRouter(prefix='/analyticss', tags=['Analytics'])
logger = create_logger(__name__)

@analytics_router.post("", status_code=201, response_model=success_response)
async def create_analytics(
    payload: analytics_schemas.AnalyticsBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new analytics"""

    analytics = Analytics.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Analytics with id {analytics.id} created')

    return success_response(
        message=f"Analytics created successfully",
        status_code=201,
        data=analytics.to_dict()
    )


@analytics_router.get("", status_code=200)
async def get_analyticss(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all analyticss"""

    query, analyticss, count = Analytics.fetch_by_field(
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
        items=[analytics.to_dict() for analytics in analyticss],
        endpoint='/analyticss',
        page=page,
        size=per_page,
        total=count,
    )


@analytics_router.get("/{id}", status_code=200, response_model=success_response)
async def get_analytics_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a analytics by ID or unique_id in case ID fails."""

    analytics = Analytics.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched analytics successfully",
        status_code=200,
        data=analytics.to_dict()
    )


@analytics_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_analytics(
    id: str,
    payload: analytics_schemas.UpdateAnalytics,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a analytics"""

    analytics = Analytics.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Analytics with id {analytics.id} updated')

    return success_response(
        message=f"Analytics updated successfully",
        status_code=200,
        data=analytics.to_dict()
    )


@analytics_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_analytics(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a analytics"""

    Analytics.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

