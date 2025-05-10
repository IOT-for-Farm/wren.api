import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel


class Sale(BaseTableModel):
    __tablename__ = 'sales'

    product_id = sa.Column(sa.String, sa.ForeignKey("products.id"), nullable=False, index=True)
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), nullable=False, index=True)

    quantity = sa.Column(sa.Integer, nullable=False)
    # total_price = sa.Column(sa.Numeric(10, 2), nullable=False)
    
    customer_name = sa.Column(sa.String)
    customer_email = sa.Column(sa.String)
    customer_phone = sa.Column(sa.String)
    customer_phone_country_code = sa.Column(sa.String)
    
    customer_id = sa.Column(sa.String, sa.ForeignKey('customers.business_partner_id'))
    vendor_id = sa.Column(sa.String, sa.ForeignKey('vendors.business_partner_id'))
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(Sale.id==foreign(TagAssociation.entity_id), TagAssociation.model_type==sales, TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==TagAssociation.tag_id, Tag.is_deleted==False)",
        backref="sales",
        lazy='selectin'
    )
    
    vendor = relationship(
        'Vendor',
        backref='sales',
        uselist=False,
        lazy='selectin'
    )
    
    customer = relationship(
        'Customer',
        backref='sales',
        uselist=False,
        lazy='selectin'
    )
    
    product = relationship(
        'Product',
        backref='sales',
        uselist=False,
        lazy='selectin'
    )
    
    organization = relationship(
        'Organization',
        backref='sales',
        uselist=False,
        lazy='selectin'
    )

    @hybrid_property
    def total_price(self):
        '''Get total price of sale'''
            
        product_price = self.product.price.selling_price
        return self.quantity * product_price
    
    @hybrid_property
    def profit(self):
        '''Get profit on sale'''
        
        profit_on_single_product = self.product.price.selling_price - self.product.price.cost_price
        return profit_on_single_product * self.quantity
