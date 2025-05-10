import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Account(BaseTableModel):
    __tablename__ = 'accounts'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"))
    
    owner_type = sa.Column(sa.String)  # "customer" or "vendor"
    owner_id = sa.Column(sa.String)      # references Customer or Vendor ID
    
    balance = sa.Column(sa.Numeric(12, 2), default=0.00)
    amount_owing = sa.Column(sa.Numeric(12, 2), default=0.00)
    amount_owed = sa.Column(sa.Numeric(12, 2), default=0.00)
    currency_code = sa.Column(sa.String(10), default='NGN')
    
    credit_limit = sa.Column(sa.Numeric(12, 2), default=0.00)
    credit_allowed = sa.Column(sa.Boolean, server_default='false')
    
    is_active = sa.Column(sa.Boolean, server_default='true')