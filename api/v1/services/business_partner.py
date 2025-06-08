from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from slugify import slugify
from sqlalchemy.orm import Session

from api.utils import helpers
from api.utils.loggers import create_logger
from api.v1.models.business_partner import BusinessPartner
from api.v1.models.contact_info import ContactInfo
from api.v1.models.location import Location
from api.v1.schemas import business_partner as business_partner_schemas
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.schemas.contact_info import ContactType
from api.v1.services.auth import AuthService


logger = create_logger(__name__)

class BusinessPartnerService:
    
    @classmethod
    def create_business_partner(
        cls,
        db: Session,
        payload: business_partner_schemas.BusinessPartnerBase,
        entity: Optional[AuthenticatedEntity] = None,
    ):
        '''Function to create a business partner'''
            
        # Check if email already exists in the organization
        existing_email_in_org = BusinessPartner.fetch_one_by_field(
            db=db, throw_error=False,
            email=payload.email,
            organization_id=payload.organization_id,
            partner_type=payload.partner_type
        )
        
        if existing_email_in_org:
            raise HTTPException(400, 'Email already exists for a business partner in organization')
        
        if payload.partner_type == 'vendor' and not payload.company_name:
            raise HTTPException(400, 'Vendors must have a company name')
        
        if not payload.unique_id:
            payload.unique_id = helpers.generate_unique_id(
                db=db, 
                organization_id=payload.organization_id,
            )
        
        if not payload.slug and payload.company_name:
            payload.slug = f'{payload.unique_id}-{slugify(payload.company_name)}'
        
        if payload.additional_info:
            payload.additional_info = helpers.format_additional_info_create(payload.additional_info)
            
        if payload.password:
            payload.password = AuthService.hash_secret(payload.password)
        
        if not payload.image_url:
            payload.image_url = helpers.generate_logo_url(f"{payload.first_name} {payload.last_name}")

        # user_id = None
        # if entity and entity.type == 'user':
        #     user_id = entity.entity.id
        
        business_partner = BusinessPartner.create(
            db=db,
            user_id=entity.entity.id if (entity is not None and entity.type=='user') else None,
            **payload.model_dump(
                exclude_unset=True, 
                exclude=['state', 'city', 'country', 'address', 'postal_code']
            )
        )
        
        # Create email contact info
        ContactInfo.create(
            db=db,
            model_name='business_partners',
            model_id=business_partner.id,
            contact_type=ContactType.EMAIL.value,
            contact_data=payload.email,
            is_primary=True
        )
        logger.info('Email contact info added for business_partner')
        
        # Create phone number contact info
        if payload.phone and payload.phone_country_code:
            ContactInfo.create(
                db=db,
                model_name='business_partners',
                model_id=business_partner.id,
                contact_type=ContactType.PHONE.value,
                contact_data=payload.phone,
                phone_country_code=payload.phone_country_code,
                is_primary=True
            )
            logger.info('Phone contact info added for business_partner')
        
        if payload.address:
            # Create business_partner location
            Location.create(
                db=db,
                model_name='business_partners',
                model_id=business_partner.id,
                **payload.model_dump(
                    exclude_unset=True,
                    include=['state', 'city', 'country', 'address', 'postal_code']
                )
            )
            logger.info('Location added for business_partner')
        
        
        return business_partner
    
    
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str, create_token: bool=True):
        
        business_partner = BusinessPartner.fetch_one_by_field(db=db, email=email)
        
        if not business_partner:
            raise HTTPException(status_code=400, detail="Invalid user credentials")

        if not business_partner.is_active:
            raise HTTPException(403, "Account is inactive")
        
        if not business_partner.password:
            raise HTTPException(400, 'You do not have a password. Try another login method')
        
        if business_partner.password and not AuthService.verify_hash(password, business_partner.password):
            raise HTTPException(status_code=400, detail="Invalid user credentials")
        
        if create_token:
            access_token = AuthService.create_access_token(db, business_partner.id, business_partner.partner_type)
            refresh_token = AuthService.create_refresh_token(db, business_partner.id, business_partner.partner_type)
            
            return business_partner, access_token, refresh_token
        
        return business_partner, None, None
