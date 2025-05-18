from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.event import Event
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.event import EventService
from api.v1.schemas import event as event_schemas
from api.utils.loggers import create_logger


event_router = APIRouter(prefix='/events', tags=['Event'])
logger = create_logger(__name__)

@event_router.post("", status_code=201, response_model=success_response)
async def create_event(
    payload: event_schemas.EventBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new event"""

    event = Event.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Event with id {event.id} created')

    return success_response(
        message=f"Event created successfully",
        status_code=201,
        data=event.to_dict()
    )


@event_router.get("", status_code=200)
async def get_events(
    search: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all events"""

    query, events, count = Event.fetch_by_field(
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
        items=[event.to_dict() for event in events],
        endpoint='/events',
        page=page,
        size=per_page,
        total=count,
    )


@event_router.get("/{id}", status_code=200, response_model=success_response)
async def get_event_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a event by ID or unique_id in case ID fails."""

    event = Event.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched event successfully",
        status_code=200,
        data=event.to_dict()
    )


@event_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_event(
    id: str,
    payload: event_schemas.UpdateEvent,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a event"""

    event = Event.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Event with id {event.id} updated')

    return success_response(
        message=f"Event updated successfully",
        status_code=200,
        data=event.to_dict()
    )


@event_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_event(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a event"""

    Event.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

