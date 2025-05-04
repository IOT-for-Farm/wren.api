import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Inventory(BaseTableModel):
    __tablename__ = 'inventory'
    
    product_id = sa.Column(sa.String, sa.ForeignKey("products.id"), nullable=False, index=True)
    variant_id = sa.Column(sa.String, sa.ForeignKey("product_variants.id"))
    
    # Stock Levels
    current_quantity = sa.Column(sa.Integer, default=0)
    initial_quantity = sa.Column(sa.Integer, default=0)  # Reserved for orders
    
    # Replenishment
    reorder_threshold = sa.Column(sa.Integer)  # amount to notify the user when there is need to restock
    reorder_amount = sa.Column(sa.Integer)
    
    # Cost Tracking
    cost_price = sa.Column(sa.Numeric(10, 2))
    selling_price = sa.Column(sa.Numeric(10, 2))
    
    currency_code = sa.Column(sa.String(10), nullable=True, index=True)
    
    # Relationships
    product = relationship("Product")
    variant = relationship("ProductVariant")


