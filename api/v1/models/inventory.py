import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

from api.core.base.base_model import BaseTableModel


class Inventory(BaseTableModel):
    __tablename__ = 'inventory'
    
    product_id = sa.Column(sa.String, sa.ForeignKey("products.id"), nullable=False, index=True)
    variant_id = sa.Column(sa.String, sa.ForeignKey("product_variants.id"))
    
    # Stock Levels
    quantity = sa.Column(sa.Integer, default=0)
    
    # Replenishment
    reorder_threshold = sa.Column(sa.Integer)  # amount to notify the organization when there is need to restock
    reorder_amount = sa.Column(sa.Integer)
    
    # Cost Tracking
    # cost_price = sa.Column(sa.Numeric(10, 2))
    # selling_price = sa.Column(sa.Numeric(10, 2))
    
    # currency_code = sa.Column(sa.String(10), nullable=True, index=True)
    
    is_active = sa.Column(sa.Boolean, default=True)
    
    # Relationships
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    @hybrid_property
    def cost_price(self):
        if self.product.price:
            return self.product.price.cost_price
    
    @hybrid_property
    def selling_price(self):
        if self.product.price:
            return self.product.price.selling_price
        
    @hybrid_property
    def currency_code(self):
        if self.product.price:
            return self.product.price.currency
    
    @hybrid_property
    def inventory_value(self):
        if not self.product.price:
            return 0.00
        else:
            return self.product.price.selling_price * self.quantity

    @hybrid_method
    def decrease_quantity(cls, number: str):
        cls.current_quantity -= number
        
    def to_dict(self, excludes=[]):
        return {
            'cost_price': self.cost_price,
            'selling_price': self.selling_price,
            'currency_code': self.currency_code,
            'inventory_value': self.inventory_value,
            **super().to_dict(excludes+['product', 'variant']),
        }
