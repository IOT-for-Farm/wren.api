from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.location import Location
from api.v1.services.auth import AuthService
from api.v1.services.location import LocationService
from api.v1.schemas import location as location_schemas
from api.utils.loggers import create_logger
from api.v1.schemas.auth import AuthenticatedEntity


location_router = APIRouter(prefix='/locations', tags=['Location'])
logger = create_logger(__name__)

@location_router.post("", status_code=201, response_model=success_response)
async def create_location(
    payload: location_schemas.LocationBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new location

    Args:
        payload: Payload for creating a new location.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """

    location = Location.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Location created successfully",
        status_code=200,
        data=location.to_dict()
    )


@location_router.get("", status_code=200)
async def get_locations(
    model_name: str = None,
    model_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all locations"""
    
    query, locations, count = Location.fetch_by_field(
        db, 
        search_fields={},
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        model_name=model_name,
        model_id=model_id,
    )
    
    return paginator.build_paginated_response(
        items=[{**location.to_dict(),} for location in locations],
        endpoint='/locations',
        page=page,
        size=per_page,
        total=count,
    )


@location_router.get("/{id}", status_code=200, response_model=success_response)
async def get_location_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a location by ID or unique_id in case ID fails.
    Args:
        id (str): ID of the location to retrieve.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """

    location = Location.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched location successfully",
        status_code=200,
        data=location.to_dict()
    )


@location_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_location(
    id: str,
    payload: location_schemas.UpdateLocation,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a location

    Args:
        id (str): ID of the location to update.
        payload: Payload for updating the location.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """

    location = Location.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Location updated successfully",
        status_code=200,
        data=location.to_dict()
    )


@location_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_location(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a location

    Args:
        id (str): ID of the location to delete.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """

    Location.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )

