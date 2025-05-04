import secrets
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.apikey import Apikey
from api.v1.models.organization import OrganizationRole
from api.v1.schemas import apikey as apikey_schemas
from api.v1.services.auth import AuthService
from api.v1.services.organization import OrganizationService


logger = create_logger(__name__)

class ApikeyService:
    
    @classmethod
    def generate_apikey(cls):
        key = secrets.token_hex(32)
        prefix = key[:8]
        key_hash = AuthService.hash_secret(key)
        
        return key, prefix, key_hash
    
    @classmethod
    def create(cls, db: Session, payload: apikey_schemas.ApikeyBase, user_id: str):
        '''Function to create and save the apikey'''
        
        if payload.access_type == apikey_schemas.AccessType.FULL.value:
            if payload.role_id:
                raise HTTPException(400, 'role_id is not needed when access type is set to full')
            
            # Automatically assign admin role
            role = OrganizationRole.fetch_one_by_field(
                db=db, throw_error=False,
                organization_id='-1',
                role_name='Admin'
            )
            payload.role_id=role.id
        
        # Check if role id is not provided when access type is set to limited
        if payload.access_type == apikey_schemas.AccessType.LIMITED.value and not payload.role_id:
            raise HTTPException(400, 'role_id is needed when access type is set to limited')
        
        if payload.role_id:
            # Check if role id exists in the organization or in the default organization
            OrganizationService.role_exists_in_org(db, payload.organization_id, payload.role_id)
        
        apikey, prefix, apikey_hash = cls.generate_apikey()
        
        apikey_obj = Apikey.create(
            db=db,
            prefix=prefix,
            key_hash=apikey_hash,
            user_id=user_id,
            **payload.model_dump(exclude_unset=True, exclude=['access_type'])
        )
        
        return apikey_obj, apikey
    
    
    @classmethod
    def create_superadmin_apikey(cls, db: Session):
        '''Function to create a superadmin apikey'''
            
        # Automatically assign superadmin role
        role = OrganizationRole.fetch_one_by_field(
            db=db, throw_error=False,
            organization_id='-1',
            role_name='Superadmin'
        )
        
        apikey, prefix, apikey_hash = cls.generate_apikey()
        
        apikey_obj = Apikey.create(
            db=db,
            prefix=prefix,
            key_hash=apikey_hash,
            role_id=role.id,
            app_name=secrets.token_hex(5)
        )
        
        return apikey_obj, apikey
