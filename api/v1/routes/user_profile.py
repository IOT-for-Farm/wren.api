# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from api.db.database import get_db
# from api.utils.settings import settings
# from api.utils.loggers import create_logger
# from api.utils.responses import success_response
# from api.utils.telex_notification import TelexNotification
# from api.v1.models.user import User
# from api.v1.models.user_profile import UserProfile
# from api.v1.schemas import user as user_schemas
# from api.v1.schemas.user_profile import UserProfileBase
# from api.v1.services.auth import AuthService
# from api.v1.services.user import UserService
# from api.v1.services.user_profile import UserProfileService


# user_profile_router = APIRouter(prefix='/profile', tags=['User Profile'])
# logger = create_logger(__name__)

# @user_profile_router.get('/me', status_code=200, response_model=success_response)
# async def get_current_entity_profile(
#     db: Session=Depends(get_db), 
#     user: User=Depends(AuthService.get_current_entity)
# ):
#     """Endpoint to get the current user's profile

#     Args:
#         db (Session, optional): Database session. Defaults to Depends(get_db).
#         user (User, optional): Current user. Defaults to Depends(AuthService.get_current_entity).
#     """
    
#     user_profile = UserProfile.fetch_one_by_field(db, user_id=user.id)
    
#     return success_response(
#         status_code=200,
#         message='User profile fetched successfully',
#         data={
#             'profile': user_profile.to_dict()
#         }
#     )
    

# @user_profile_router.patch('/update', status_code=200, response_model=success_response)
# async def update_user_profile(
#     payload: UserProfileBase,
#     db: Session=Depends(get_db), 
#     entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
# ):
#     """Endpoint to update the current user's profile

#     Args:
#         payload (UserProfileBase): Payload containing first_name, last_name, email and password
#         db (Session, optional): Database session. Defaults to Depends(get_db).
#         entity (User, optional): Current user. Defaults to Depends(AuthService.get_current_entity).
#     """
    
#     user_profile = UserProfileService.update_profile(db, entity.id, payload)
    
#     return success_response(
#         status_code=200,
#         message='User profile updated successfully',
#         data={
#             'profile': user_profile.to_dict()
#         }
#     )