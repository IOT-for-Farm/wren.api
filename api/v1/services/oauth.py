from datetime import datetime
from fastapi import BackgroundTasks, HTTPException, Request
import requests
from sqlalchemy.orm import Session
from config import config

from api.db.database import get_db
from api.utils.loggers import create_logger
from api.utils.telex_notification import TelexNotification
from api.v1.models.user import User
from api.v1.schemas.auth import CreateUser
from api.v1.services.user import UserService
from api.v1.services.auth import AuthService


logger = create_logger(__name__)

class GoogleOauthService:
    """Handles database operations for google oauth"""

    @classmethod
    def authenticate(cls, db: Session, id_token: str):
        """Authenticate user with Google OAuth"""
        
        profile_endpoint = f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}'
        profile_response = requests.get(profile_endpoint)
        
        if profile_response.status_code != 200:
            logger.error(f"Failed to fetch user info: {profile_response.text}\nStatus code: {profile_response.status_code}")
            raise HTTPException(status_code=profile_response.status_code, detail="Invalid token or failed to fetch user info")
        
        profile_data = profile_response.json()

        email = profile_data.get('email')
        user = User.fetch_one_by_field(db=db, throw_error=False, email=email)
        
        # Check if the user exists
        if user:
            if not user.is_active:
                raise HTTPException(403, "Account is inactive")
            
            # User already exists, return their details
            access_token = AuthService.create_access_token(db, user_id=user.id)
            refresh_token = AuthService.create_refresh_token(db, user_id=user.id)
        else:
            # Create user
            user, access_token, refresh_token = UserService.create(
                db=db,
                payload = CreateUser(
                    email=email,
                    first_name=profile_data.get('given_name'),
                    last_name=profile_data.get('family_name'),
                    profile_picture=profile_data.get('picture'),
                    is_superuser=False
                )
            )
            
        # Update last_login of user
        user = User.update(db, user.id, last_login=datetime.now())
        
        return user, access_token, refresh_token
    
    @classmethod
    def callback(cls, db: Session, request: Request):
        code = request.query_params.get("code")

        if not code:
            raise HTTPException(status_code=400, detail="Authorization code is missing")
    
        # Exchange the authorization code for an access token
        token_url = "https://oauth2.googleapis.com/token"
        token_response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config("GOOGLE_REDIRECT_URI"),
                "client_id": config("GOOGLE_CLIENT_ID"),
                "client_secret": config("GOOGLE_CLIENT_SECRET"),
            },
        )

        if token_response.status_code != 200:
            logger.error(f"Failed to fetch token: {token_response.text}\nStatus code: {token_response.status_code}")
            raise HTTPException(status_code=token_response.status_code, detail="Failed to exchange authorization code")
        
        token_data = token_response.json()
        id_token = token_data.get("id_token")
        
        # Authenticate user
        user, access_token, refresh_token = cls.authenticate(db=db, id_token=id_token)
        return user, access_token, refresh_token
