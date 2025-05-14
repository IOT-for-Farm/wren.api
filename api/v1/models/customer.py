import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel
from api.v1.models.business_partner import BusinessPartner


class Customer(BaseTableModel):
    __tablename__ = 'customers'
    
    business_partner_id = sa.Column(
        sa.String, 
        sa.ForeignKey('business_partners.id'),
        primary_key=True,
        nullable=False, index=True
    )
    
    language = sa.Column(sa.String)
    gender = sa.Column(sa.String)
    age = sa.Column(sa.Integer)
    
    customer_type = sa.Column(sa.String, default="individual")  # individual/business
    industry = sa.Column(sa.String, nullable=True)

    # Future tracking fields
    # last_purchase_date = sa.Column(sa.DateTime, nullable=True)
    # loyalty_points = sa.Column(sa.Integer, default=0)
    preferred_payment_method = sa.Column(sa.String, nullable=True)
    
    business_partner = relationship(
        'BusinessPartner',
        lazy='selectin',
        backref='customer',
        uselist=False
    )
    
    accounts = relationship(
        'Account',
        primaryjoin='and_(Customer.id==foreign(Account.owner_id), Account.is_deleted==False)',
        backref='customer_accounts',
        lazy='selectin',
    )
