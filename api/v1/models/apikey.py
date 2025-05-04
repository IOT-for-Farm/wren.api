import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Apikey(BaseTableModel):
    __tablename__ = 'apikeys'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    role_id = sa.Column(sa.String, sa.ForeignKey("organization_roles.id"))
    
    key_hash = sa.Column(sa.String, nullable=False, index=True)
    prefix= sa.Column(sa.String(8), nullable=False, unique=True)
    app_name = sa.Column(sa.String, index=True)
    is_active = sa.Column(sa.Boolean, server_default="true")
    last_used_at = sa.Column(sa.DateTime)
    
    # Relationships
    organization = relationship("Organization", backref="apikeys", uselist=False)
    user = relationship("User", backref="apikeys", uselist=False)
    role = relationship('OrganizationRole', backref='apikeys', lazy='selectin')
    
    def to_dict(self, excludes = ...):
        return super().to_dict(excludes=['key_hash'])
