from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.contact_info import ContactInfo
from api.v1.services.auth import AuthService
from api.v1.services.contact_info import ContactInfoService
from api.v1.schemas import contact_info as contact_info_schemas
from api.utils.loggers import create_logger
from api.v1.schemas.auth import AuthenticatedEntity


contact_info_router = APIRouter(prefix='/contact-infos', tags=['Contact Info'])
logger = create_logger(__name__)

# @contact_info_router.post("", status_code=201, response_model=success_response)
# async def create_contact_info(
#     organization_id: str,
#     payload: contact_info_schemas.ContactInfoBase,
#     db: Session=Depends(get_db), 
#     entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
# ):
#     """Endpoint to create a new contact_info

#     Args:
#         payload: Payload for creating a new contact_info.
#         db (Session, optional): DB session. Defaults to Depends(get_db).
#         entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
#     """
    
#     AuthService.has_org_permission(
#         entity=entity,
#         organization_id=organization_id,
#         permission='contact_info:create',
#         db=db
#     )

#     contact_info = ContactInfo.create(
#         db=db,
#         **payload.model_dump(exclude_unset=True)
#     )

#     return success_response(
#         message=f"Contact info created successfully",
#         status_code=200,
#         data=contact_info.to_dict()
#     )


# @contact_info_router.get("", status_code=200)
# async def get_contact_infos(
#     model_name: str = None,
#     model_id: str = None,
#     page: int = 1,
#     per_page: int = 10,
#     sort_by: str = 'created_at',
#     order: str = 'desc',
#     db: Session=Depends(get_db), 
#     entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
# ):
#     """Endpoint to get all contact_infos

#     Args:
#         search (str, optional): Search query. Defaults to None.
#         page (int, optional): Page number. Defaults to 1.
#         per_page (int, optional): Number of items per page. Defaults to 10.
#         sort_by (str, optional): Field to sort by. Defaults to 'created_at'.
#         order (str, optional): Order of sorting. Defaults to 'desc'.
#         db (Session, optional): DB session. Defaults to Depends(get_db).
#         entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
#     """
    
#     # AuthService.belongs_to_organization(
#     #     entity=entity,
#     #     organization_id=id,
#     #     db=db
#     # )

#     query, contact_infos, count = ContactInfo.fetch_by_field(
#         db, 
#         sort_by=sort_by,
#         order=order.lower(),
#         page=page,
#         per_page=per_page,
#         model_name=model_name,
#         model_id=model_id,
#     )
    
#     return paginator.build_paginated_response(
#         items=[{**contact_info.to_dict(),} for contact_info in contact_infos],
#         endpoint='/contact-infos',
#         page=page,
#         size=per_page,
#         total=count,
#     )


# @contact_info_router.get("/{id}", status_code=200, response_model=success_response)
# async def get_contact_info_by_id(
#     id: str,
#     db: Session=Depends(get_db), 
#     entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
# ):
#     """Endpoint to get a contact_info by ID or unique_id in case ID fails.
#     Args:
#         id (str): ID of the contact_info to retrieve.
#         db (Session, optional): DB session. Defaults to Depends(get_db).
#         entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
#     """

#     contact_info = ContactInfo.fetch_by_id(db, id)
    
#     return success_response(
#         message=f"Fetched contact info successfully",
#         status_code=200,
#         data=contact_info.to_dict()
#     )


# @contact_info_router.patch("/{id}", status_code=200, response_model=success_response)
# async def update_contact_info(
#     id: str,
#     organization_id: str,
#     payload: contact_info_schemas.UpdateContactInfo,
#     db: Session=Depends(get_db), 
#     entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
# ):
#     """Endpoint to update a contact_info

#     Args:
#         id (str): ID of the contact_info to update.
#         payload: Payload for updating the contact_info.
#         db (Session, optional): DB session. Defaults to Depends(get_db).
#         entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
#     """
    
#     AuthService.has_org_permission(
#         entity=entity,
#         organization_id=organization_id,
#         permission='contact_info:update',
#         db=db
#     )

#     contact_info = ContactInfo.update(
#         db=db,
#         id=id,
#         **payload.model_dump(exclude_unset=True)
#     )

#     return success_response(
#         message=f"Contact info updated successfully",
#         status_code=200,
#         data=contact_info.to_dict()
#     )


# @contact_info_router.delete("/{id}", status_code=200, response_model=success_response)
# async def delete_contact_info(
#     id: str,
#     organization_id: str,
#     db: Session=Depends(get_db), 
#     entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
# ):
#     """Endpoint to delete a contact_info

#     Args:
#         id (str): ID of the contact_info to delete.
#         db (Session, optional): DB session. Defaults to Depends(get_db).
#         entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
#     """
    
#     AuthService.has_org_permission(
#         entity=entity,
#         organization_id=organization_id,
#         permission='contact_info:delete',
#         db=db
#     )

#     ContactInfo.soft_delete(db, id)

#     return success_response(
#         message=f"Deleted successfully",
#         status_code=200,
#         data={"id": id}
#     )

