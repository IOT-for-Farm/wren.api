from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator
from api.v1.models.activity_log import ActivityLog
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.utils.loggers import create_logger


activity_log_router = APIRouter(prefix='/activity-logs', tags=['Activity Logs'])
logger = create_logger(__name__)


@activity_log_router.get("", status_code=200)
async def get_activity_logs(
    organization_id: str,
    model_name: str = None,
    model_id: str = None,
    model_names: str = None,
    model_ids: str = None,
    filter_by_organization: bool = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all activity logs"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='logs:view',
        organization_id=organization_id
    )

    query, activity_logs, count = ActivityLog.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        # organization_id=organization_id if filter_by_organization==True else None,
        model_name=model_name,
        model_id=model_id,
    )
    
    if filter_by_organization and filter_by_organization == True:
        query = query.filter(ActivityLog.organization_id == organization_id)
    else:
        query = query.filter(
            or_(
                ActivityLog.organization_id == organization_id,
                ActivityLog.organization_id == None,
            )
        )
    
    if model_names:
        model_list = [model_name.strip() for model_name in model_names.split(",")]
        query = query.filter(ActivityLog.model_name.in_(model_list))
    
    if model_ids:
        id_list = [model_id.strip() for model_id in model_ids.split(",")]
        query = query.filter(ActivityLog.model_id.in_(id_list))
    
    activity_logs, count = paginator.paginate_query(query, page, per_page)
    
    return paginator.build_paginated_response(
        items=[activity_log.to_dict() for activity_log in activity_logs],
        endpoint='/activity-logs',
        page=page,
        size=per_page,
        total=count,
    )
