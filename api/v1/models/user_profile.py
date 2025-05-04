# import sqlalchemy as sa
# from sqlalchemy.orm import relationship

# from api.core.base.base_model import BaseTableModel


# class UserProfile(BaseTableModel):
#     __tablename__ = 'user_profile'
    
#     first_name = sa.Column(sa.String, nullable=True)
#     last_name = sa.Column(sa.String, nullable=True)
#     username = sa.Column(sa.String, nullable=True)
#     profile_picture = sa.Column(sa.String, nullable=True)
#     phone_number = sa.Column(sa.String, nullable=True)
#     phone_country_code = sa.Column(sa.String, nullable=True)
#     city = sa.Column(sa.String, nullable=True)
#     state = sa.Column(sa.String, nullable=True)
#     country = sa.Column(sa.String, nullable=True)
#     bio = sa.Column(sa.Text, nullable=True)
#     address = sa.Column(sa.Text, nullable=True)
    
#     user_id = sa.Column(sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), index=True)
#     user = relationship('User', back_populates='profile')
