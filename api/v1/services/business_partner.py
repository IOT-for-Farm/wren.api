from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.business_partner import BusinessPartner
from api.v1.schemas import business_partner as business_partner_schemas
from api.v1.services.auth import AuthService


logger = create_logger(__name__)

class BusinessPartnerService:
    
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str, create_token: bool=True):
        
        business_partner = BusinessPartner.fetch_one_by_field(db=db, email=email)
        
        if not business_partner:
            raise HTTPException(status_code=400, detail="Invalid user credentials")

        if not business_partner.is_active:
            raise HTTPException(403, "Account is inactive")
        
        if not business_partner.password:
            raise HTTPException(400, 'You do not have a password. You cannot login')
        
        if business_partner.password and not AuthService.verify_hash(password, business_partner.password):
            raise HTTPException(status_code=400, detail="Invalid user credentials")
        
        if create_token:
            access_token = AuthService.create_access_token(db, business_partner.id)
            refresh_token = AuthService.create_refresh_token(db, business_partner.id)
            
            return business_partner, access_token, refresh_token
        
        return business_partner, None, None
