import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.order import OrderStatus


class Order(BaseTableModel):
    __tablename__ = "orders"
    
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    invoice_id = sa.Column(sa.String, sa.ForeignKey("invoices.id"), nullable=True)
    
    customer_name = sa.Column(sa.String)
    customer_email = sa.Column(sa.String)
    customer_phone = sa.Column(sa.String)
    customer_phone_country_code = sa.Column(sa.String)
    
    customer_id = sa.Column(sa.String, sa.ForeignKey('customers.business_partner_id'))
    
    # total_amount = sa.Column(sa.Numeric(12, 2), nullable=False)
    currency_code = sa.Column(sa.String(10), default='NGN')
    
    status = sa.Column(sa.String, default=OrderStatus.pending.value, index=True)
    
    items = relationship('OrderItem', back_populates='order', lazy='selectin')
    customer = relationship(
        'Customer',
        backref='orders',
        uselist=False,
        lazy='selectin'
    )
    
    @hybrid_property
    def total_amount(self):
        '''Get total amount of items in order'''
        
        total = 0.00
        for item in self.items:
            total += item.product.price.selling_price if self.product.prise else 0.00
        
        return total
    

class OrderItem(BaseTableModel):
    __tablename__ = "order_items"
    
    order_id = sa.Column(sa.String, sa.ForeignKey("orders.id"), index=True)
    product_id = sa.Column(sa.String, sa.ForeignKey("products.id"), index=True)
    quantity = sa.Column(sa.Integer)
    
    product = relationship('Product', backref='product_orders', uselist=False, lazy='selectin')
    order = relationship('Order', back_populates='items')
