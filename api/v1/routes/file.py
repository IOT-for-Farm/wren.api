import os
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from slugify import slugify
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.file import File as FileModel, Folder
from api.v1.services.auth import AuthService
from api.v1.services.file import FileService
from api.v1.schemas import file as file_schemas
from api.utils.loggers import create_logger
from api.v1.schemas.auth import AuthenticatedEntity


file_router = APIRouter(tags=['Files & Folders'])
logger = create_logger(__name__)

@file_router.post("/files", status_code=201, response_model=success_response)
async def create_file(
    payload: file_schemas.FileBase = Form(media_type='multipart/form-data'),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new file

    Args:
        payload: Payload for creating a new file.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=payload.organization_id,
        permission='file:upload',
        db=db
    )

    file_obj = await FileService.upload_file(
        db=db,
        # file_to_upload=payload.file,
        payload=payload
    )
    
    logger.info(f'File {file_obj.file_name} created at {file_obj.file_path}')

    return success_response(
        message=f"File created successfully",
        status_code=201,
        data=file_obj.to_dict()
    )


@file_router.get("/files", status_code=200)
async def get_files(
    organization_id: str,
    model_name: str = None,
    model_id: str = None,
    file_name: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all files

    Args:
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )
    
    query, files, count = FileModel.fetch_by_field(
        db, 
        search_fields={
            'file_name': file_name,
        },
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        organization_id=organization_id,
        model_name=model_name,
        model_id=model_id,
    )
    
    return paginator.build_paginated_response(
        items=[file.to_dict() for file in files],
        endpoint='/files',
        page=page,
        size=per_page,
        total=count,
    )


@file_router.get("/files/{id}", status_code=200, response_model=success_response)
async def get_file_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a file by ID or unique_id in case ID fails.
    Args:
        id (str): ID of the file to retrieve.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """

    file = FileModel.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=file.organization_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched file successfully",
        status_code=200,
        data=file.to_dict()
    )


@file_router.patch("/files/{id}", status_code=200, response_model=success_response)
async def update_file(
    id: str,
    organization_id: str,
    payload: file_schemas.UpdateFile = Form(media_type='multipart/form-data'),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a file

    Args:
        id (str): ID of the file to update.
        payload: Payload for updating the file.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='file:update',
        db=db
    )
    
    file_instance = FileModel.fetch_by_id(db, id)
    
    if payload.file:
        file_obj = await FileService.upload_file(
            db=db,
            payload=file_schemas.FileBase(
                file=payload.file,
                organization_id=file_instance.organization_id,
                model_name=file_instance.model_name,
                model_id=file_instance.model_id,
                description=payload.description if payload.description else None,
                label=payload.label if payload.label else None
            ),
            add_to_db=False
        )
        os.remove(file_instance.file_path)
        
        updated_file = FileModel.update(
            db=db,
            id=id,
            file_name=file_obj['file_name'],
            file_path=file_obj['file_path'],
            file_size=file_obj['file_size'],
            url=file_obj['url'],
            description=payload.description if payload.description else None,
            label=payload.label if payload.label else None
            # **file_obj,
        )
         
    else:
        updated_file = FileModel.update(
            db=db,
            id=id,
            **payload.model_dump(exclude_unset=True)
        )

    logger.info(f'File updated to {updated_file.file_name} at {updated_file.file_path}')
    
    return success_response(
        message=f"File updated successfully",
        status_code=200,
        data=updated_file.to_dict()
    )


@file_router.delete("/files/{id}", status_code=200, response_model=success_response)
async def delete_file(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a file

    Args:
        id (str): ID of the file to delete.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='file:delete',
        db=db
    )
    
    file = FileModel.fetch_by_id(db, id)
    
    os.remove(file.file_path)

    FileModel.hard_delete(db, id)

    return success_response(
        message=f"Deleted {id} successfully",
        status_code=200,
        data={"id": id}
    )


@file_router.post("/folders", status_code=201, response_model=success_response)
async def create_folder(
    payload: file_schemas.FolderBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new folder"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=payload.organization_id,
        permission='folder:create',
        db=db
    )

    folder = Folder.create(
        db=db,
        slug=slugify(payload.name),
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Folder created successfully",
        status_code=201,
        data=folder.to_dict()
    )


@file_router.get("/folders", status_code=200)
async def get_folders(
    organization_id: str,
    name: str = None,
    slug: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all folders"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, folders, count = Folder.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        organization_id=organization_id,
        slug=slug,
    )
    
    return paginator.build_paginated_response(
        items=[folder.to_dict() for folder in folders],
        endpoint='/folders',
        page=page,
        size=per_page,
        total=count,
    )


@file_router.get("/folders/{id}", status_code=200, response_model=success_response)
async def get_folder_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a folder by ID or unique_id in case ID fails."""

    folder = Folder.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=folder.organization_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched folder successfully",
        status_code=200,
        data=folder.to_dict()
    )


@file_router.get("/folders/{id}/contents", status_code=200, response_model=success_response)
async def get_folder_by_id(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a folder's contents"""
    

    data = FileService.get_folder_contents(db=db, folder_id=id, organization_id=organization_id)
    
    return success_response(
        message=f"Fetched folder contents successfully",
        status_code=200,
        data=data
    )
    

@file_router.patch("/folders/{id}", status_code=200, response_model=success_response)
async def update_folder(
    id: str,
    organization_id: str,
    payload: file_schemas.UpdateFolder,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a folder"""

    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='folder:update',
        db=db
    )
    
    folder = Folder.fetch_by_id(db, id)
    
    if payload.parent_id == folder.id:
        raise HTTPException(400, 'Folder cannot be its parent')
    
    updated_folder = Folder.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f'Folder updated to {updated_folder.name}')
    return success_response(
        message=f"Folder updated successfully",
        status_code=200,
        data=updated_folder.to_dict()
    )


@file_router.delete("/folders/{id}", status_code=200, response_model=success_response)
async def delete_folder(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a folder"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='folder:delete',
        db=db
    )
    
    # Delete folder contents
    FileService.delete_folder_contents(
        db=db,
        folder_id=id,
        organization_id=organization_id
    )

    Folder.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )
