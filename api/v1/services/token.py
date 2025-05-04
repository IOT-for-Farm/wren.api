import datetime as dt
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from api.utils.loggers import create_logger
from api.utils.settings import settings
from api.v1.models.token import BlacklistedToken, Token


logger = create_logger(__name__)

class TokenService:
    
    @classmethod
    def create_token(
        cls, 
        db: Session, 
        token_type: str, 
        expiry_in_minutes: int,
        user_id: Optional[str]=None,
        payload={}
    ):
        
        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=expiry_in_minutes)
        data = {
            **payload,
            "user_id": user_id, 
            "exp": expires, 
            "type": token_type
        }
        
        # Remove user_id from payload if it is None
        if not user_id:
            del data["user_id"]
            
        encoded_jwt = jwt.encode(data, settings.SECRET_KEY, settings.ALGORITHM)
        
        Token.create(
            db=db,
            token=encoded_jwt,
            token_type=token_type,
            expiry_time=expires,
            user_id=user_id
        )
        return encoded_jwt
    
    @classmethod
    def revoke_token(cls, db: Session, token: str, user_id: str):
        """Function to revoke token"""
        
        token_obj = Token.fetch_one_by_field(db=db, token=token)
        BlacklistedToken.create(db=db, token=token_obj.token, user_id=user_id)
        Token.hard_delete(db=db, id=token_obj.id)
        
        
    @classmethod
    def check_and_revoke_existing_token(cls, db: Session, user_id: str, token_type: str):
        '''Function c=to check if a token exists and revoke the token'''
        
        # Check if user has a token already and it has not expired
        existing_token = Token.fetch_one_by_field(
            db=db, throw_error=False, 
            user_id=user_id, token_type=token_type
        )
        
        if existing_token:
            # Blacklist the token and delete it
            BlacklistedToken.create(db=db, token=existing_token.token, user_id=user_id)
            Token.hard_delete(db, existing_token.id)

    
    @classmethod
    def decode_and_verify_token(
        cls, 
        db: Session, 
        token: str, 
        expected_token_type: str,
        credentials_exception,
        check_user_id_in_payload: bool = True
    ):
        '''Function to decode and verify a token'''
        
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("user_id")
            jwt_payload_token_type = payload.get("type")
            
            # Check if token is blackliosted
            blacklisted_token = BlacklistedToken.fetch_one_by_field(db=db, throw_error=False, token=token)

            if check_user_id_in_payload and not user_id:
                raise credentials_exception
            
            if blacklisted_token is not None:
                raise credentials_exception
                
            if jwt_payload_token_type != expected_token_type:
                raise HTTPException(detail=f"Token of type '{expected_token_type}' expected. Got '{jwt_payload_token_type}'", status_code=400)

        except JWTError as err:
            logger.error(err)
            raise credentials_exception

        return payload