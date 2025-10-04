from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session, backref
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.product import ProductStatus, ProductType


class Product(BaseTableModel):
    __tablename__ = "products"

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    creator_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    vendor_id = sa.Column(sa.String)
    parent_id = sa.Column(sa.String, sa.ForeignKey('products.id', ondelete="cascade"), index=True, nullable=True)
    
    name = sa.Column(sa.String, index=True, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    slug = sa.Column(sa.String, nullable=True, index=True, unique=True)
    status = sa.Column(sa.String, nullable=False, default=ProductStatus.UNPUBLISHED.value, index=True)
    type = sa.Column(sa.String, nullable=False, default=ProductType.PHYSICAL.value, index=True)
    is_available = sa.Column(sa.Boolean, default=True)
    
    # previous_slugs = sa.Column(sa.JSON, default=[])
    attributes = sa.Column(sa.JSON, nullable=True, default={})
    additional_info = sa.Column(sa.JSON, nullable=True, default={})
    
    creator = relationship(
        'User',
        backref='created_products',
        uselist=False,
        lazy='selectin'
    )
    
    vendor = relationship(
        'Vendor',
        backref='products',
        uselist=False,
        lazy='selectin',
        primaryjoin='foreign(Product.vendor_id)==Vendor.business_partner_id'
    )
    
    photos = relationship(
        'File',
        backref='product_photos',
        primaryjoin='and_(Product.id == foreign(File.model_id), File.is_deleted == False, Product.organization_id==File.organization_id)',
        lazy='selectin',
        viewonly=True
    )
    
    # parent = relationship(
    #     "Product", 
    #     remote_side='Product.id', 
    #     uselist=False, 
    #     foreign_keys=[parent_id],
    #     lazy='selectin',
    #     backref=backref('sub_products',  cascade="all, delete-orphan"), 
    #     post_update=True, 
    #     single_parent=True, 
    # )
    
    categories = relationship(
        'Category',
        secondary='category_association',
        primaryjoin='and_(foreign(CategoryAssociation.entity_id)==Product.id, '
                   'CategoryAssociation.is_deleted==False, '
                   'CategoryAssociation.model_type=="products")',
        secondaryjoin='and_(Category.id==foreign(CategoryAssociation.category_id), '
                     'Category.is_deleted==False)',
        lazy='selectin',
        backref='products',
        viewonly=True
    )
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(Product.id==foreign(TagAssociation.entity_id), "
                   "TagAssociation.model_type=='products', "
                   "TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==foreign(TagAssociation.tag_id), "
                     "Tag.is_deleted==False)",
        backref="products",
        lazy='selectin',
        viewonly=True
    )
    
    price = relationship(
        'ProductPrice',
        backref='products',
        uselist=False,
        primaryjoin='and_(ProductPrice.product_id==Product.id, ProductPrice.is_active==True)',
        lazy='selectin',
        viewonly=True
    )
    
    inventory = relationship(
        'Inventory',
        backref='product_invetory',
        uselist=False,
        primaryjoin='and_(Inventory.product_id==Product.id, Inventory.is_active==True)',
        lazy='selectin',
        viewonly=True
    )
    
    def to_dict(self, excludes=[]):
        data = super().to_dict(excludes)
        data['inventory'] = self.inventory.to_dict() if self.inventory else None
        return data
    

class ProductVariant(BaseTableModel):
    __tablename__ = 'product_variants'
    
    product_id = sa.Column(sa.String, sa.ForeignKey("products.id"), index=True)
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    
    name = sa.Column(sa.String, nullable=False)
    slug = sa.Column(sa.String, nullable=True, index=True, unique=True)
    description = sa.Column(sa.Text, nullable=True)
    attributes = sa.Column(sa.JSON, default={})
    
    photos = relationship(
        'File',
        backref='product_variant_photos',
        primaryjoin='and_(ProductVariant.id == foreign(File.model_id), File.is_deleted == False, ProductVariant.organization_id==File.organization_id)',
        lazy='selectin',
        viewonly=True
    )
    
    price = relationship(
        'ProductPrice',
        backref='product_variants',
        uselist=False,
        primaryjoin='and_(ProductPrice.variant_id==ProductVariant.id, ProductPrice.is_active==True)',
        lazy='selectin',
        viewonly=True
    )
    
    inventory = relationship(
        'Inventory',
        backref='product_variant_inventory',
        uselist=False,
        primaryjoin='and_(Inventory.variant_id==ProductVariant.id, Inventory.is_active==True)',
        lazy='selectin',
        viewonly=True
    )
    
    def to_dict(self, excludes=[]):
        data = super().to_dict(excludes)
        return data
    

class ProductPrice(BaseTableModel):
    __tablename__ = 'product_prices'
    
    product_id = sa.Column(sa.String, sa.ForeignKey('products.id'), index=True, nullable=False)
    variant_id = sa.Column(sa.String, sa.ForeignKey("product_variants.id"))
    
    cost_price = sa.Column(sa.Numeric(10, 2), nullable=False, default=0.0) 
    selling_price = sa.Column(sa.Numeric(10, 2), nullable=False, default=0.0) 
    currency = sa.Column(sa.String(5), default="NGN")
    
    start_date = sa.Column(sa.DateTime, server_default=sa.func.now())
    end_date = sa.Column(sa.DateTime)
    
    min_quantity = sa.Column(sa.Integer, default=1)  # Tiered pricing
    
    is_active = sa.Column(sa.Boolean, default=True)  # Tiered pricing
    
    notes = sa.Column(sa.Text)
    
    # Relationships
    product = relationship("Product")
    variant = relationship("ProductVariant")

    # @hybrid_property
    # def is_active_price(cls):
    #     if (cls.start_date and cls.end_date) and cls.is_active:
    #         return cls.start_date < datetime.now() and cls.end_date > datetime.now()
        
    #     elif (cls.start_date and not cls.end_date) and cls.is_active:
    #         return cls.start_date < datetime.now()
        
    #     return cls.is_active
    
    # @hybrid_property
    # def is_active_price(self):
    #     return self.start_date < datetime.now() and self.end_date > datetime.now()

    # @is_active_price.expression
    # def is_active_price(cls):
    #     return (cls.start_date < datetime.now()) & (cls.end_date > datetime.now())
