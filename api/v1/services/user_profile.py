# from sqlalchemy.orm import Session

# from api.utils.loggers import create_logger
# from api.v1.models.user_profile import UserProfile
# from api.v1.schemas.user_profile import UserProfileBase


# logger = create_logger(__name__)

# class UserProfileService:
#     @classmethod
#     def update_profile(
#         cls,
#         db: Session,
#         user_id: str,
#         payload: UserProfileBase
#     ):
#         """Updates the user profile"""
        
#         # Get the user profile
#         user_profile = UserProfile.fetch_one_by_field(db, user_id=user_id)
        
#         # Update user profile
#         user_profile = UserProfile.update(
#             db, 
#             user_profile.id, 
#             **payload.model_dump(exclude_unset=True)
#         )
        
#         # Update profile picture
#         user_profile.profile_picture = (
#             f'https://ui-avatars.com/api/?name={user_profile.first_name} {user_profile.last_name}'
#             if user_profile.first_name and user_profile.last_name
#             else f'https://ui-avatars.com/api/?name={user_profile.username}'
#         )
#         db.commit()
#         db.refresh(user_profile)
        
#         return user_profile
