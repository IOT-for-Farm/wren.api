import sqlalchemy as sa, enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel


class TokenType(enum.Enum):
    
    ACCESS = 'access'
    REFRESH = 'refresh'
    MAGIC = 'magic_link'
    PASSWORD_RESET = 'password_reset'
    ACCOUNT_REACTIVATION = 'reactivate_account'
    ORG_INVITE = 'organization_invite'
    

class Token(BaseTableModel):
    __tablename__ = 'tokens'
    
    token = sa.Column(sa.String, nullable=False)
    token_type = sa.Column(sa.String, server_default=TokenType.ACCESS.value)
    expiry_time = sa.Column(sa.DateTime, nullable=False)
    
    user_id = sa.Column(sa.String, nullable=True)
    # user_id = sa.Column(sa.String, sa.ForeignKey('users.id'), nullable=True)
    # user = relationship('User', backref='tokens')
    
    # @hybridproperty
    def is_expired(self):
        return self.expiry_time < sa.func.now()


class BlacklistedToken(BaseTableModel):
    __tablename__ = 'blacklisted_tokens'
    
    token = sa.Column(sa.String, nullable=False)
    
    # user_id = sa.Column(sa.String, sa.ForeignKey('users.id'), nullable=True)
    user_id = sa.Column(sa.String, nullable=True)
    # user = relationship('User', backref='blacklisted_tokens')
