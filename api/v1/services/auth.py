from typing import Any, Optional, Annotated
import datetime as dt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyQuery
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from config import config

from api.core.dependencies.email_sending_service import send_email
from api.db.database import get_db
from api.utils.loggers import create_logger
from api.utils.settings import settings
from api.v1.models.apikey import Apikey
from api.v1.models.organization import Organization, OrganizationMember, OrganizationRole
from api.v1.models.token import BlacklistedToken, Token, TokenType
from api.v1.models.user import User
from api.v1.schemas.auth import AuthenticatedEntity, EntityType
from api.v1.schemas.token import TokenData
from api.v1.services.token import TokenService


bearer_scheme = HTTPBearer(auto_error=False)
apikey_scheme = APIKeyQuery(name="apikey", auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = create_logger(__name__)


class AuthService:
    
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str, create_token: bool=True):
        
        user = User.fetch_one_by_field(db=db, email=email)
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid user credentials")

        if not user.is_active:
            # TODO: Reactivate user if possible
            raise HTTPException(403, "Account is inactive")
        
        if not user.password:
            raise HTTPException(400, 'You do not have a password. Try magic login or another available authentication method')
        
        if user.password and not cls.verify_hash(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid user credentials")
        
        # Update last_login of user
        user = User.update(db, user.id, last_login=dt.datetime.now())
        
        if create_token:
            access_token = cls.create_access_token(db, user.id)
            refresh_token = cls.create_refresh_token(db, user.id)
            
            return user, access_token, refresh_token
        
        return user, None, None
    
    @classmethod
    def hash_secret(cls, secret: str):
        return pwd_context.hash(secret)
    
    @classmethod
    def verify_hash(cls, secret: str, hash: str):
        return pwd_context.verify(secret, hash)
    
    @classmethod
    def create_access_token(cls, db: Session, user_id: str):
        
        # Check if user has a token already
        TokenService.check_and_revoke_existing_token(db, user_id=user_id, token_type=TokenType.ACCESS.value)
        
        encoded_jwt = TokenService.create_token(
            db=db,
            token_type=TokenType.ACCESS.value,
            expiry_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user_id=user_id
        )
        return encoded_jwt

    @classmethod
    def create_refresh_token(cls, db: Session, user_id: str):
        
        # Check if user has a token already and it has not expired
        TokenService.check_and_revoke_existing_token(db, user_id=user_id, token_type=TokenType.REFRESH.value)
        
        encoded_jwt = TokenService.create_token(
            db=db,
            token_type=TokenType.REFRESH.value,
            expiry_in_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
            user_id=user_id
        )
        return encoded_jwt
    
    @classmethod
    def verify_token(cls, db: Session, token: str, expected_token_type: str, credentials_exception):
        """Base function to verify a token to get the user id"""
        
        payload = TokenService.decode_and_verify_token(
            db=db,
            token=token,
            expected_token_type=expected_token_type,
            credentials_exception=credentials_exception
        )
        
        user_id = payload.get("user_id")
        return user_id
        
    
    @classmethod
    def verify_access_token(cls, db: Session, access_token: str, credentials_exception):
        """Funtcion to decode and verify access token"""
        
        user_id = cls.verify_token(
            db=db,
            token=access_token,
            expected_token_type=TokenType.ACCESS.value,
            credentials_exception=credentials_exception
        )
        
        token_data = TokenData(user_id=user_id)
        return token_data

    @classmethod
    def verify_refresh_token(cls, db: Session, refresh_token: str, credentials_exception):
        """Funtcion to decode and verify refresh token"""
        
        user_id = cls.verify_token(
            db=db,
            token=refresh_token,
            expected_token_type=TokenType.REFRESH.value,
            credentials_exception=credentials_exception
        )
        
        token_data = TokenData(user_id=user_id)
        return token_data
    
    @classmethod
    def refresh_access_token(cls, db: Session, current_refresh_token: str):
        """Function to generate new access token and rotate refresh token"""

        credentials_exception = HTTPException(
            status_code=401, detail="Refresh token expired"
        )

        token = cls.verify_refresh_token(
            db=db, 
            refresh_token=current_refresh_token, 
            credentials_exception=credentials_exception
        )

        if token:
            access = cls.create_access_token(db=db, user_id=token.user_id)
            refresh = cls.create_refresh_token(db=db, user_id=token.user_id)

            return access, refresh
    
    @classmethod
    def logout(cls, db: Session, user_id: str):
        """Function to log a user out of their account"""
        
        # get both access and refresh tokens of the user
        access_token_obj = Token.fetch_one_by_field(db=db, user_id=user_id, token_type='access')
        refresh_token_obj = Token.fetch_one_by_field(db=db, user_id=user_id, token_type='refresh')
        
        # Revoke both tokens
        TokenService.revoke_token(db, access_token_obj.token, user_id)
        TokenService.revoke_token(db, refresh_token_obj.token, user_id)
        
    @classmethod
    def send_magic_link(cls, db: Session, email: str, bg_tasks: BackgroundTasks):
        """Function to send magic link to user"""
        
        user = User.fetch_one_by_field(db=db, email=email)
        
        # Check and revoke existing token
        TokenService.check_and_revoke_existing_token(db, user_id=user.id, token_type=TokenType.MAGIC.value)
        
        expiry_minutes = 15
        # Generate a magic link token
        magic_link_token = TokenService.create_token(
            db=db, 
            token_type=TokenType.MAGIC.value,
            expiry_in_minutes=expiry_minutes,
            user_id=user.id,
        )
        
        # TODO: Update the url
        bg_tasks.add_task(
            send_email,
            recipients=[user.email],
            template_name='magic-login.html',
            subject='Securely log in to your account',
            template_data={
                'user': user,
                'magic_link': f"{config('AUTH_APP_URL')}/magic/verify",
                'token': magic_link_token,
                'expiry_minutes': expiry_minutes
            }
        )
        
        return magic_link_token

    @classmethod
    def verify_magic_token(cls, db:Session, token: str):
        """Function to verify the magic link token"""
        
        credentials_exception = HTTPException(
            status_code=401, detail="Invalid token"
        )
        
        user_id = cls.verify_token(
            db=db,
            token=token,
            expected_token_type=TokenType.MAGIC.value,
            credentials_exception=credentials_exception
        )
        
        user = User.fetch_by_id(db, user_id)
        access_token = cls.create_access_token(db, user.id)
        refresh_token = cls.create_refresh_token(db, user.id)
        
        # Revoke token
        TokenService.revoke_token(db, token, user_id)

        return user, access_token, refresh_token
    
    
    @classmethod
    async def send_password_reset_link(cls, db: Session, email: str, bg_tasks: BackgroundTasks):
        """Function to send password reset token to user"""
        
        user = User.fetch_one_by_field(db=db, email=email)
        
        # Check and revoke existing token
        TokenService.check_and_revoke_existing_token(db, user_id=user.id, token_type=TokenType.PASSWORD_RESET.value)
        
        expiry_minutes = 15
        # Generate a password reset token
        password_reset_token = TokenService.create_token(
            db=db, 
            token_type=TokenType.PASSWORD_RESET.value,
            expiry_in_minutes=expiry_minutes,
            user_id=user.id,
        )
        
        # TODO: Update the url
        bg_tasks.add_task(
            send_email,
            recipients=[user.email],
            template_name='password-reset.html',
            subject='Password Reset',
            template_data={
                'user': user,
                'reset_utl': f"{config('AUTH_APP_URL')}/password-reset",
                'token': password_reset_token,
                'expiry_minutes': expiry_minutes
            }
        )
        
        return password_reset_token

    @classmethod
    def verify_password_reset_token(cls, db:Session, token: str):
        """Function to verify the password reset token"""
        
        credentials_exception = HTTPException(
            status_code=401, detail="Invalid token"
        )
        
        user_id = cls.verify_token(
            db=db,
            token=token,
            expected_token_type=TokenType.PASSWORD_RESET.value,
            credentials_exception=credentials_exception
        )
        
        TokenService.revoke_token(db, token, user_id)
        
        return user_id

    @classmethod
    def get_current_entity(
        cls, 
        token: HTTPAuthorizationCredentials = Depends(bearer_scheme), 
        apikey: str = Depends(apikey_scheme),
        db: Session = Depends(get_db)
    ):
        """Function to get current logged-in entity (appikey or user)"""
        
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        if token:
            user = cls._validate_token(db, token, credentials_exception)
            return AuthenticatedEntity(type=EntityType.USER, entity=user)
            
        if apikey:
            apikey = cls._validate_apikey(db, apikey, credentials_exception)
            return AuthenticatedEntity(type=EntityType.APIKEY, entity=apikey)
    
    
    @classmethod
    def get_current_user_entity(
        cls, 
        token: HTTPAuthorizationCredentials = Depends(bearer_scheme), 
        db: Session = Depends(get_db)
    ):
        """Function to get current logged-in user"""
        
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        user = cls._validate_token(db, token, credentials_exception)
        # return user
        return AuthenticatedEntity(type=EntityType.USER, entity=user)

    
    @classmethod
    def get_current_apikey_entity(
        cls, 
        apikey: str = Depends(apikey_scheme),
        db: Session = Depends(get_db)
    ):
        """Function to get current logged-in user"""
        
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
            
        apikey_obj = cls._validate_apikey(db, apikey, credentials_exception)
        # return apikey.organization
        return AuthenticatedEntity(type=EntityType.APIKEY, entity=apikey_obj)
        
    
    @classmethod
    def _validate_token(cls, db: Session, token: HTTPAuthorizationCredentials, credentials_exception):
        '''THis function validates the access token'''
        
        try:
            # Extract the token from the HTTPBearer credentials
            token_str = token.credentials

            # Verify the token
            token_data = cls.verify_access_token(
                db=db, 
                access_token=token_str, 
                credentials_exception=credentials_exception
            )
            
            user = User.fetch_by_id(db, token_data.user_id)
            
            if not user.is_active:
                raise HTTPException(403, "Account is inactive")
            
            return user
        
        except AttributeError:
            raise credentials_exception
        
        except Exception as e:
            logger.error(e)
            raise credentials_exception
    
    
    @classmethod
    def _validate_apikey(cls, db: Session, apikey: str, credentials_exception):
        '''This function validates api key'''
        
        try:
            prefix = apikey[:8]
            
            apikey_obj = Apikey.fetch_one_by_field(
                db=db, throw_error=False,
                prefix=prefix,
                is_active=True
            )
            
            if apikey_obj and cls.verify_hash(apikey, apikey_obj.key_hash):
                apikey_obj.last_used_at = dt.datetime.now(dt.timezone.utc)
                db.commit()
                db.refresh(apikey_obj)
                return apikey_obj
            
            raise credentials_exception
        
        except Exception as e:
            logger.error(e)
            raise credentials_exception
    
    
    @classmethod
    def get_current_superuser(
        cls, 
        access_token: HTTPAuthorizationCredentials = Depends(bearer_scheme), 
        apikey: str = Depends(apikey_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Function to get current logged-in user"""
        
        entity = cls.get_current_entity(access_token, apikey, db)
        
        if entity.type == EntityType.USER:
            user: User = entity.entity
        
            if not user.is_superuser:
                logger.info('User is not a superuser')
                raise HTTPException(403, "You do not have access to use this resource")
            
            return user
        
        if entity.type == EntityType.APIKEY:
            apikey_obj: Apikey = entity.entity
            
            role = OrganizationRole.fetch_one_by_field(
                db=db, throw_error=False,
                organization_id='-1',
                id=apikey_obj.role_id
            )
        
            # Check if apikey has superadmin role
            if not role.role_name == 'Superadmin':
                logger.info('Apikey is not a superadmin key')
                raise HTTPException(403, "You do not have access to use this resource")
            
            return apikey_obj
    
    @classmethod
    def belongs_to_organization(
        cls, 
        entity: AuthenticatedEntity,
        organization_id: str,
        db: Session = Depends(get_db)
    ):
        '''Function to check if an authenticated endtity belongs to an organization'''
        
        # if not entity:
        #     raise HTTPException(401, 'Unauthenticated')
        
        # Cgeck if organization exists
        org = Organization.fetch_by_id(db, organization_id)
        
        if entity.type == EntityType.USER:
            user: User = entity.entity
        
            if user.is_superuser:
                return True
            
            # Check if user exists in organization
            org_user_exists = OrganizationMember.fetch_one_by_field(
                db=db, throw_error=False,
                organization_id=org.id,
                user_id=user.id
            )
            
            if org_user_exists:
                return True
        
        if entity.type == EntityType.APIKEY:
            # Check if apikey has superadmin role
            apikey: Apikey = entity.entity
            
            role = OrganizationRole.fetch_one_by_field(
                db=db, throw_error=False,
                id=apikey.role_id,
                organization_id='-1',
            )
        
            if role.role_name == 'Superadmin':
                return True
            
            # Check if apikey exists for organization
            apikey_exists_in_org = Apikey.fetch_one_by_field(
                db=db, throw_error=False,
                id=apikey.id,
                prefix=apikey.prefix,
                organization_id=org.id
            )
            
            if apikey_exists_in_org:
                return True
        
        logger.info(f'Entity ({entity.type.value}) does not belong to this organization')
        raise HTTPException(403, 'You do not have the permission to access this resource')    
        
    
    @classmethod
    def has_org_permission(
        cls, 
        entity: AuthenticatedEntity,
        organization_id: str,
        permission: str,
        db: Session = Depends(get_db)
    ):
        '''Function to check if an authenticated endtity has the permission to handle an action'''
        
        # Check if entity belongs to organization first
        cls.belongs_to_organization(entity, organization_id, db)
        
        if entity.type == EntityType.USER:
            user: User = entity.entity
        
            if user.is_superuser:
                return True  
            
            org_user = OrganizationMember.fetch_one_by_field(
                db=db, throw_error=False,
                organization_id=organization_id,
                user_id=user.id
            )
            
            # Extract list or permissions from org user roles
            role = org_user.role
            permissions = role.permissions
        
        if entity.type == EntityType.APIKEY:
            # Check if apikey has superadmin role
            apikey: Apikey = entity.entity
            
            role = OrganizationRole.fetch_one_by_field(
                db=db, throw_error=False,
                organization_id='-1',
                id=apikey.role_id
            )
        
            if role.role_name == 'Superadmin':
                return True
            
            permissions = apikey.role.permissions
            
        if permission in permissions:
            return True
        
        logger.info(f'Entity ({entity.type.value}) with role `{role.role_name}` does not have `{permission}` in the list of permissions:\n{permissions}')
        raise HTTPException(403, 'You do not have the permission to access this resource')    
