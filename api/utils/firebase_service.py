import os, pyrebase
from sqlalchemy.orm import Session
from config import config

from api.core.dependencies.firebase_config import firebase_config
from api.v1.models.file import File
from api.v1.schemas.file import FileBase
from api.v1.services.file import FileService


class FirebaseService:
    
    @classmethod
    async def upload_file(
        cls, 
        db: Session,
        file,
        allowed_extensions: list | None, 
        upload_folder: str, 
        model_id: str,
        file_label: str = None,
        file_description: str = None,
    ):
        '''Function to upload a file'''
        
        new_file = await FileService.upload_file(
            db=db,
            file_to_upload=file,
            payload=FileBase(
                model_id=model_id,
                model_name=upload_folder,
                label=file_label,
                description=file_description
            ),
            allowed_extensions=allowed_extensions
        )
        
        # Initailize firebase
        firebase = pyrebase.initialize_app(firebase_config)
        
        # Set up storage and a storage path for each file
        storage = firebase.storage()
        firebase_storage_path = f'{config("APP_NAME")}/{upload_folder}/{model_id}/{new_file.file_name}'
        
        # Store the file in the firebase storage path
        storage.child(firebase_storage_path).put(new_file.file_path)
        
        # Get download URL
        download_url = storage.child(firebase_storage_path).get_url(None)
        
        # Update file url
        File.update(
            db=db,
            id=new_file.id,
            url=download_url
        )
        
        return download_url


    # async def upload_file(
    #     cls, 
    #     file,
    #     allowed_extensions: list | None, 
    #     upload_folder: str, 
    #     model_id: str
    # ):
    #     '''Function to upload a file'''
        
    #     # Check against invalid extensions
    #     file_name = file.filename.lower()
        
    #     file_extension = file_name.split('.')[-1]
    #     name = file_name.split('.')[0]
        
    #     if not file:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail='File not provided'
    #         )

    #     if allowed_extensions:
    #         if file_extension not in allowed_extensions:
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail=f'File extension {file_extension} not allowed'
    #             )
                
    #     os.makedirs(settings.TEMP_DIR, exist_ok=True)
        
    #     # Generate a new file name
    #     new_filename = f'{name}-{token_hex(5)}.jpg'
        
    #     # Save file temporarily
    #     save_path = os.path.join(settings.TEMP_DIR, new_filename)
        
    #     with open(save_path, 'wb') as f:
    #         content = await file.read()
    #         f.write(content)
        
    #     # Initailize firebase
    #     firebase = pyrebase.initialize_app(firebase_config)
        
    #     # Set up storage and a storage path for each file
    #     storage = firebase.storage()
    #     firebase_storage_path = f'greentrac/{upload_folder}/{model_id}/{new_filename}'
        
    #     # Store the file in the firebase storage path
    #     storage.child(firebase_storage_path).put(save_path)
        
    #     # Get download URL
    #     download_url = storage.child(firebase_storage_path).get_url(None)
        
    #     # Delete the temporary file
    #     os.remove(save_path)
        
    #     return download_url
