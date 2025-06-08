from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from config import config

from api.core.dependencies.email_sending_service import send_email
from api.db.database import get_db
from api.utils import paginator
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.services.auth import AuthService
from api.v1.services.user import UserService
from api.v1.schemas import user as user_schemas
from api.utils.loggers import create_logger
from api.utils.telex_notification import TelexNotification
from api.v1.schemas.auth import AuthenticatedEntity


user_router = APIRouter(prefix='/users', tags=['User'])
logger = create_logger(__name__)

@user_router.get('/', status_code=200)
async def get_users(
    email: str = None,
    first_name: str = None,
    last_name: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    user: User=Depends(AuthService.get_current_superuser)
):
    """Endpoint to get the current user

    Args:
        db (Session, optional): Database session. Defaults to Depends(get_db).
        user (User, optional): Current user. Defaults to Depends(AuthService.get_current_superuser).
    """
    
    query, users, count = User.all(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        },
    )
    
    return paginator.build_paginated_response(
        items=[user.to_dict(excludes=['password', 'is_superuser']) for user in users],
        endpoint='/users',
        page=page,
        size=per_page,
        total=count,
    )
        
    # return paginator.build_model_paginated_response(
    #     db,
    #     model=User,
    #     endpoint='/users',
    #     page=page,
    #     size=per_page,
    #     order=order,
    #     sort_by=sort_by,
    #     search_fields={
    #         'email': search,
    #     },
    #     excludes=['password', 'is_superuser']
    # )

@user_router.get('/me', status_code=200, response_model=success_response)
async def get_current_user(db: Session=Depends(get_db), entity: User=Depends(AuthService.get_current_user_entity)):
    """Endpoint to get the current user

    Args:
        db (Session, optional): Database session. Defaults to Depends(get_db).
        user (User, optional): Current user. Defaults to Depends(AuthService.get_current_entity).
    """
    
    return success_response(
        status_code=200,
        message='User fetched successfully',
        data=entity.entity.to_dict()
    )
    
@user_router.get('/{user_id}', status_code=200, response_model=success_response)
async def get_user_by_id(
    user_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_superuser)
):
    """Endpoint to get a user by ID or unique_id in case ID fails.

    Args:
        user_id (str): ID of the user to be fetched
        db (Session, optional): Database session. Defaults to Depends(get_db).
        entity (User, optional): Current user. Defaults to Depends(AuthService.get_current_entity).
    """
    
    user = User.fetch_by_id(db, user_id)
    
    return success_response(
        status_code=200,
        message='User fetched successfully',
        data=user.to_dict(excludes=['password', 'is_superuser'])
    )

@user_router.patch('/me', status_code=200, response_model=success_response)
async def update_user_details(
    payload: user_schemas.UpdateUser,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to a user to update their details"""
    
    if payload.password and payload.old_password:
        payload.password = UserService.verify_password_change(
            db, 
            email=payload.email,
            old_password=payload.old_password,
            new_password=payload.password
        ) 
    
    if payload.email and payload.email != entity.email:
        user = User.fetch_one_by_field(db, throw_error=False, email=payload.email)
        if user:
            raise HTTPException(400, 'Email already in use')
    
    user = User.update(
        db,
        id=entity.id,
        **payload.model_dump(exclude_unset=True)
    )
            
    return success_response(
        status_code=200,
        message='Details updated successfully',
        data=user.to_dict()
    )

@user_router.post('/deactivate-account', status_code=200, response_model=success_response)
async def deactivate_account(
    bg_tasks: BackgroundTasks,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint for a user to deactivate their account"""
    
    user = User.update(db, entity.id, is_active=False)
    
    # TODO: Implement account deletion logic after retention days have passed. See email template to understand
    bg_tasks.add_task(
        send_email,
        recipients=[user.email],
        template_name='deactivae-account-success.html',
        subject='Account Deactivated',
        template_data={
            'user': user,
            'data_retention_days': 7,
            'reversal_days': 3,
            'deactivation_date': datetime.now().date().strftime("%d %B %Y"),  # change to user.deactivation_date
        }
    )
    
    return success_response(
        status_code=200,
        message='Account deactivated'
    )
    
@user_router.post('/reactivate-account/request', status_code=200, response_model=success_response)
async def reactivate_account_request(
    bg_tasks: BackgroundTasks,
    payload: user_schemas.AccountReactivationRequest,
    db: Session=Depends(get_db),
):
    """Endpoint to request for account reactivation token"""
    
    token = await UserService.send_account_reactivation_token(db, payload.email, bg_tasks)
    
    return success_response(
        status_code=200,
        message='Account reactivation token sent',
        # TODO: Remove this
        data={
            'token': token
        }
    )
    
@user_router.get('/reactivate-account', status_code=200, response_model=success_response)
async def reactivate_account(
    bg_tasks: BackgroundTasks,
    token: str,
    db: Session=Depends(get_db),
):
    """Endpoint to reactivate account"""
    
    user_id = UserService.verify_account_reactivation_token(db, token)
    
    user = User.update(db, user_id, is_active=True)
    
    # TODO: Update the url
    bg_tasks.add_task(
        send_email,
        recipients=[user.email],
        template_name='account-reactivate-success.html',
        subject='Account reactivated successfully',
        template_data={
            'user': user,
            'reactivation_date': datetime.now().date().strftime("%d %B %Y"),
            'dashboard_url': config('APP_DASHBOARD_URL'),
        }
    )
        
    return success_response(
        status_code=200,
        message='Account reactivated successfully'
    )

@user_router.delete('/delete-account', status_code=200, response_model=success_response)
async def delete_account(
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delet account"""
    
    User.soft_delete(db, entity.id)
    
    return success_response(
        status_code=200,
        message='Account deleted'
    )

@user_router.delete('/{user_id}', status_code=200, response_model=success_response)
async def delete_user(
    user_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_superuser)
):
    """Endpoint to delet user account. Accessible only to superusers"""
    
    User.soft_delete(db, user_id)
    
    return success_response(
        status_code=200,
        message='User deleted'
    )
