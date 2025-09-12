import os
import secrets
import sqlalchemy as sa
from typing import List
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from config import config

from api.utils.loggers import create_logger
from api.v1.models.file import File, Folder
from api.v1.schemas.file import FileBase


logger = create_logger(__name__)

class FileService:
    
    @classmethod
    async def upload_file(
        cls, 
        db: Session, 
        # payload.file: UploadFile, 
        payload: FileBase,
        allowed_extensions: List[str] = [],
        add_to_db: bool = True
    ):
        """Upload a file to the server and save its metadata to the database."""
        
        # Check if the file is empty
        if payload.file.file is None:
            raise HTTPException(
                status_code=400, 
                detail="File is empty"
            )
        
        # Check if file extension is allowed
        filename = payload.file.filename
        file_extension = filename.split('.')[-1]
        if allowed_extensions:
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File extension '{file_extension}' is not allowed. Allowed extensions are: {', '.join(allowed_extensions)}"
                )
        
        # Check for file size
        max_file_size_mb = config("FILE_UPLOAD_LIMIT_MB", cast=int, default=5)
        max_file_size =  int(max_file_size_mb) * 1024 * 1024
        
        if payload.file.size > max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds the limit of {max_file_size_mb} MB"
            )
        
        # Build file path
        new_filename = f'{payload.file_name}.{file_extension}' if payload.file_name else  f'{filename.split('.')[0]}_{secrets.token_hex(8)}.{file_extension}'
        new_filename = new_filename.replace(' ', '_')
        STORAGE_DIR = config("FILESTORAGE", default="filestorage")
        file_path = f"{STORAGE_DIR}/{payload.organization_id}/{payload.model_name}/{payload.model_id}/{new_filename}"
        
        # Create directories if they do not exist
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Error creating directory for file storage"
            )
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            buffer.write(payload.file.file.read())
            
        logger.info(f"File saved to {file_path}")
        
        file_url = f"{config('API_URL')}/{file_path}" if not payload.url else payload.url,  # TODO: fix up. generate url by uploading to a storage location
        if add_to_db:
            # Find the highest position for the given model_name and possible model_id
             query = (
                db.query(sa.func.max(File.position))
                .filter(File.model_name == payload.model_name)
            )
            
        if payload.model_id:
            query = query.filter(File.model_id == payload.model_id)
            
            max_position = query.scalar() or 0
            
            # Save file metadata to database
            file_instance = File.create(
                db,
                organization_id=payload.organization_id,
                position=max_position+1,
                file_name=new_filename,
                file_path=file_path,
                file_size=payload.file.size,
                model_id=payload.model_id,
                model_name=payload.model_name,
                url=file_url,
                description=payload.description if payload.description else None,
                label=payload.label if payload.label else None
            )
            
            return file_instance
        
        else:
            return {
                'file_name': new_filename,
                'file_path': file_path,
                'url': file_url,
                'file_size': payload.file.size
            }

    
    @classmethod
    async def bulk_upload(
        cls, 
        db: Session, 
        files: List[UploadFile],
        organization_id: str,
        model_id: str,
        model_name: str,
        allowed_extensions: List[str] = [],
        add_to_db: bool = True
    ):
        '''Fucntion to handle bulk upload of files'''
        
        file_instances = []
        
        for file in files:
            file_instance = await cls.upload_file(
                db=db,
                payload=FileBase(
                    file=file,
                    model_name=model_name,
                    model_id=model_id,
                    organization_id=organization_id,
                ),
                allowed_extensions=allowed_extensions,
                add_to_db=add_to_db
            )
            
            file_instances.append(file_instance)
        
        return file_instances
    
    
    @classmethod
    def get_folder_contents(
        cls,
        db: Session, 
        folder_id: str, 
        organization_id: str
    ):
        '''THis function gets all folder contents ie sub-folders and files'''
        
        query, folders, folder_count = Folder.fetch_by_field(
            db=db,
            paginate=False,
            parent_id=folder_id,
            organization_id=organization_id
        )
        
        query, files, file_count = File.fetch_by_field(
            db=db,
            paginate=False,
            model_name='folders',
            model_id=folder_id,
            organization_id=organization_id
        )
        
        total_count = folder_count + file_count
        
        return {
            'folders': folders,
            'files': files,
            'file_count': file_count,
            'folder_count': folder_count,
            'total': total_count
        }

    
    @classmethod
    def delete_folder_contents(
        cls,
        db: Session, 
        folder_id: str, 
        organization_id: str
    ):
        
        data = cls.get_folder_contents(db=db, folder_id=folder_id, organization_id=organization_id)
        
        files = data['files']
        folders = data['folders']
        
        for file in files:
            file.is_deleted = True
        
        for folder in folders:
            folder.is_deleted = True
        
        db.commit()

    
    @classmethod
    def move_file_to_position(cls, db: Session, file_id: str, new_position: int):
        # Get the file to move
        file = File.fetch_by_id(db, file_id)

        current_position = file.position
        model_name = file.model_name
        model_id = file.model_id

        if new_position == current_position:
            return  # No change needed

        # Shift positions of other files accordingly
        if new_position < current_position:
            # Moving up: shift others down
            query = db.query(File).filter(
                File.model_name == model_name,
                File.position >= new_position,
                File.position < current_position,
                File.id != file.id
            )
            
            if model_id:
                query = query.filter(File.model_id == model_id)
            
            query.update({File.position: File.position + 1}, synchronize_session="fetch")
        else:
            # Moving down: shift others up
            query = db.query(File).filter(
                File.model_name == model_name,
                File.position <= new_position,
                File.position > current_position,
                File.id != file.id
            )
            
            if model_id:
                query = query.filter(File.model_id == model_id)
            
            query.update({File.position: File.position - 1}, synchronize_session="fetch")

        # Set new position for the dragged file
        file.position = new_position
        db.commit()
        db.refresh(file)
