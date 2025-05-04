import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class User(BaseTableModel):
    __tablename__ = 'users'
    
    email = sa.Column(sa.String, unique=True, index=True)
    password = sa.Column(sa.String, nullable=True)
    first_name = sa.Column(sa.String, nullable=True)
    last_name = sa.Column(sa.String, nullable=True)
    username = sa.Column(sa.String, nullable=True)
    profile_picture = sa.Column(sa.String, nullable=True)
    phone_number = sa.Column(sa.String, nullable=True)
    phone_country_code = sa.Column(sa.String, nullable=True)
    city = sa.Column(sa.String, nullable=True)
    state = sa.Column(sa.String, nullable=True)
    country = sa.Column(sa.String, nullable=True)
    bio = sa.Column(sa.Text, nullable=True)
    address = sa.Column(sa.Text, nullable=True)
    is_active = sa.Column(sa.Boolean, server_default='true')
    # is_verified = sa.Column(sa.Boolean, server_default='false')
    is_superuser = sa.Column(sa.Boolean, server_default='false')
    last_login = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    
    # organizations = relationship(
    #     "OrganizationMember",
    #     primaryjoin="and_(User.id == OrganizationMember.user_id, OrganizationMember.is_deleted == False)",
    #     backref="user_orgs",
    #     viewonly=True,
    #     lazy='selectin'
    # )
    
    def to_dict(self, excludes = ...):
        return super().to_dict(excludes=['password', 'is_superuser'])
