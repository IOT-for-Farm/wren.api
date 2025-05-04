from datetime import timedelta
from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from api.core.dependencies.celery.worker import send_telex_notification
from config import config

from api.db.database import get_db
from api.utils.settings import settings
from api.utils.loggers import create_logger
from api.utils.responses import success_response
from api.utils.telex_notification import TelexNotification
from api.v1.models.user import User
from api.v1.schemas import auth as auth_schemas
from api.v1.services.auth import AuthService
from api.v1.services.oauth import GoogleOauthService
from api.v1.services.user import UserService
from api.v1.schemas.auth import AuthenticatedEntity


auth_router = APIRouter(prefix='/auth', tags=['Auth'])
APP_URL = config("APP_URL")
logger = create_logger(__name__)

@auth_router.post('/register', status_code=201, response_model=success_response)
async def register(
    bg_tasks: BackgroundTasks, 
    payload: auth_schemas.CreateUser, 
    db: Session=Depends(get_db)
):
    """Endpoint to create a new user"""
    
    new_user, access_token, refresh_token = UserService.create(db, payload, bg_tasks)
        
    response = success_response(
        status_code=201,
        message='Signed up successfully',
        data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': new_user.to_dict()
        }
    )
    
    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        httponly=True,
        secure=True,
        samesite="none",
    )
    
    return response


@auth_router.post('/login', status_code=200, response_model=success_response)
async def login(payload: auth_schemas.LoginSchema, db: Session=Depends(get_db)):
    """Endpoint to log in a user

    Args:
        payload (auth_schemas.LoginSchema): Contains email and password
        db (Session, optional): _description_. Defaults to Depends(get_db).
    """
    
    user, access_token, refresh_token = AuthService.authenticate(
        db, 
        email=payload.email.lower().strip(), 
        password=payload.password
    )
    
    # TelexNotification(webhook_id='01963f75-a386-7978-bc64-5380e321a60a').send_notification(
    #     event_name='User Login',
    #     message=f'User {user.email} logged in at {user.last_login}',
    #     status='success',
    #     username='Wren Login'
    # )
    
    send_telex_notification.delay(
        webhook_id='01963f75-a386-7978-bc64-5380e321a60a',
        event_name='User Login',
        message=f'User {user.email} logged in at {user.last_login}',
        status='success',
        username='Wren Login'
    )
    
    response = success_response(
        status_code=200,
        message='Logged in successfully',
        data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    )
    
    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        httponly=True,
        secure=True,
        samesite="none",
    )
    
    return response


@auth_router.post('/magic', status_code=200, response_model=success_response)
async def magic_login(bg_tasks: BackgroundTasks, payload: auth_schemas.MagicLoginRequest, db: Session=Depends(get_db)):
    """Endpoint to request a magic login link

    Args:
        payload (auth_schemas.MagicLoginRequest): Contains email
        db (Session, optional): Database session. Defaults to Depends(get_db).
    """
    
    token = AuthService.send_magic_link(db, payload.email, bg_tasks)
    
    return success_response(
        status_code=200,
        message='Magic link sent successfully',
        # TODO: Remove this data
        data={
            'token': token,
        }
    )
    

@auth_router.get('/magic/verify', status_code=200, response_model=success_response)
async def magic_login_verify(token: str, db: Session=Depends(get_db)):
    """Endpoint to log in a user

    Args:
        token (str): Magic link token generated
        db (Session, optional): _description_. Defaults to Depends(get_db).
    """
    
    user, access_token, refresh_token = AuthService.verify_magic_token(
        db, 
        token=token,
    )
    
    TelexNotification(webhook_id='01962f17-c9fe-7902-8356-6483863464a8').send_notification(
        event_name='Magic Login',
        message=f'User {user.email} logged in at {user.last_login} with magic link',
        status='success',
        username='Wren Login'
    )
    
    response = success_response(
        status_code=200,
        message='Logged in successfully',
        data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    )
    
    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        httponly=True,
        secure=True,
        samesite="none",
    )
    
    return response


@auth_router.get("/google/initiate")
async def initiate_google_auth():
    client_id = config("GOOGLE_CLIENT_ID")
    redirect_uri = config("GOOGLE_REDIRECT_URI")
    scope = "openid email profile"
    response_type = "code"
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scope}"
    return RedirectResponse(url=auth_url, status_code=302)


@auth_router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Endpoint to handle Google OAuth callback

    Args:
        request (Request): The request object containing the authorization code
        db (Session, optional): Database session. Defaults to Depends(get_db).
    """
    
    user, access_token, refresh_token = GoogleOauthService.callback(
        db=db,
        request=request
    )
    
    response = success_response(
        status_code=200,
        message='Logged in successfully',
        data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    )
    
    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        httponly=True,
        secure=True,
        samesite="none",
    )
    
    return response


@auth_router.post("/google", status_code=200)
async def google_login(
    token_request: auth_schemas.GoogleAuth, 
    db: Session = Depends(get_db)
):
    """
    Handles Google OAuth login.

    Args:
    - token_request (GoogleAuth): OAuth token request.
    - db (Session): Database session.

    Returns:
    - JSONResponse: JSON response with user details and access token.

    Example:
    ```
    POST /google HTTP/1.1
    Content-Type: application/json

    {
        "id_token": "your_id_token_here"
    }
    ```
    """
    
    user, access_token, refresh_token = GoogleOauthService.authenticate(
        db=db,
        id_token=token_request.id_token
    )
    
    response = success_response(
        status_code=200,
        message='Logged in successfully',
        data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    )
    
    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        httponly=True,
        secure=True,
        samesite="none",
    )
    
    return response
    
    
@auth_router.post('/password-reset/request', status_code=200, response_model=success_response)
async def password_reset_request(bg_tasks: BackgroundTasks, payload: auth_schemas.ResetPasswordRequest, db: Session=Depends(get_db)):
    """Endpoint to request a password reset link

    Args:
        payload (auth_schemas.ResetPasswordRequest): Contains email
        db (Session, optional): Database session. Defaults to Depends(get_db).
    """
    
    token = await AuthService.send_password_reset_link(db, payload.email, bg_tasks)
    
    return success_response(
        status_code=200,
        message='Password reset link sent successfully',
        # TODO: Remove this data
        data={
            'token': token,
        }
    )
    
    
@auth_router.post('/password-reset', status_code=200, response_model=success_response)
async def reset_password(token: str, payload: auth_schemas.ResetPassword, db: Session=Depends(get_db)):
    """Endpoint to reset user password

    Args:
        token (str): Reset password token
        payload (auth_schemas.ResetPassword): Contains, password
        db (Session, optional): The db session. Defaults to Depends(get_db).
    """
    
    user_id = AuthService.verify_password_reset_token(db, token)
    
    # Update user password
    password_hash = AuthService.hash_secret(payload.password)
    User.update(db, id=user_id, password=password_hash)
    
    return success_response(
        status_code=200,
        message='Password reset successful'
    )


@auth_router.get('/refresh-access-token', status_code=200, response_model=success_response)
async def refresh_access_token(
    refresh_token: str=Cookie(None),
    db: Session=Depends(get_db),
):
    """Endpoint to refresh access token

    Args:
        db (Session): Database session. Defaults to Depends(get_db).
        refresh_token (str): The current refresh token in the cookies.
    """
    
    access, refresh = AuthService.refresh_access_token(db, refresh_token)
    
    response = success_response(
        status_code=200,
        message='Access token refreshed successfully',
        data={
            'access_token': access,
            'refresh_token': refresh,
        }
    )
    
    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        httponly=True,
        secure=True,
        samesite="none",
    )
    
    return response


@auth_router.post('/logout', status_code=200, response_model=success_response)
async def logout(db: Session=Depends(get_db), entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)):
    """Endpoint to log a user out

    Args:
        db (Session, optional): _description_. Defaults to Depends(get_db).
    """
    
    user: User = entity.entity
    AuthService.logout(db, user.id)
    
    response = success_response(
        status_code=200,
        message='Logged out successfully'
    )
    
    # Add refresh token to cookies
    response.delete_cookie('refresh_token')
    
    return response
