import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session, backref

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.product import ProductStatus, ProductType


class Product(BaseTableModel):
    __tablename__ = "products"

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    parent_id = sa.Column(sa.String, sa.ForeignKey('products.id', ondelete="cascade"), index=True, nullable=True)
    
    name = sa.Column(sa.String, index=True, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    slug = sa.Column(sa.String(191), nullable=True, index=True, unique=True)
    status = sa.Column(sa.String, nullable=False, default=ProductStatus.UNPUBLISHED.value, index=True)
    type = sa.Column(sa.String, nullable=False, default=ProductType.PHYSICAL.value, index=True)
    is_available = sa.Column(sa.Boolean, server_default='true')
    
    # previous_slugs = sa.Column(sa.JSON, default=[])
    attributes = sa.Column(sa.JSON, nullable=True, default={})
    additional_info = sa.Column(sa.JSON, nullable=True, default={})
    
    photos = relationship(
        'File',
        backref='product_files',
        primaryjoin='and_(Product.id == foreign(File.model_id), File.is_deleted == False)',
        lazy='selectin'
    )
    
    parent = relationship(
        "Product", 
        remote_side='Product.id', 
        uselist=False, 
        foreign_keys=[parent_id],
        lazy='selectin',
        backref=backref('sub_products',  cascade="all, delete-orphan"), 
        post_update=True, 
        single_parent=True, 
    )
    

class ProductVariant(BaseTableModel):
    __tablename__ = 'product_variants'
    
    product_id = sa.Column(sa.String, sa.ForeignKey("products.id"), index=True)
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    attributes = sa.Column(sa.JSON, default={})
    
    photos = relationship(
        'File',
        backref='product_variant_files',
        primaryjoin='and_(ProductVariant.id == foreign(File.model_id), File.is_deleted == False)',
        lazy='selectin'
    )
    

class ProductPrice(BaseTableModel):
    __tablename__ = 'product_prices'
    
    product_id = sa.Column(sa.String, sa.ForeignKey('products.id'), index=True, nullable=False)
    variant_id = sa.Column(sa.String, sa.ForeignKey("product_variants.id"))
    
    amount = sa.Column(sa.Numeric(10, 2), nulable=False, default=0.0) 
    cost_price = sa.Column(sa.Numeric(10, 2), nulable=False, default=0.0) 
    currency = sa.Column(sa.String(3), default="NGN")
    
    start_date = sa.Column(sa.DateTime, server_default=sa.func.now())
    end_date = sa.Column(sa.DateTime)
    
    min_quantity = sa.Column(sa.Integer, default=1)  # Tiered pricing
    
    # Relationships
    product = relationship("Product")
    variant = relationship("ProductVariant")
