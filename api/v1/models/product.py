import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session, backref

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.product import ProductStatus, ProductType


class Product(BaseTableModel):
    __tablename__ = "products"

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    creator_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    vendor_id = sa.Column(sa.String, sa.ForeignKey("vendors.business_partner_id"))
    parent_id = sa.Column(sa.String, sa.ForeignKey('products.id', ondelete="cascade"), index=True, nullable=True)
    
    name = sa.Column(sa.String, index=True, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    slug = sa.Column(sa.String, nullable=True, index=True, unique=True)
    status = sa.Column(sa.String, nullable=False, default=ProductStatus.UNPUBLISHED.value, index=True)
    type = sa.Column(sa.String, nullable=False, default=ProductType.PHYSICAL.value, index=True)
    is_available = sa.Column(sa.Boolean, server_default='true')
    
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
        lazy='selectin'
    )
    
    photos = relationship(
        'File',
        backref='product_photos',
        primaryjoin='and_(Product.id == foreign(File.model_id), File.is_deleted == False, Product.organization_id==File.organization_id)',
        lazy='selectin'
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
        primaryjoin='and_(CategoryAssociation.entity_id==Product.id, CategoryAssociation.is_deleted==False, CategoryAssociation.model_type==products)',
        secondaryjoin='and_(Category.id==CategoryAssociation.category_id, Category.is_deleted==False)',
        lazy='selectin',
        backref='categories'
    )
    
    # tags = relationship(
    #     "Tag",
    #     secondary='product_tags',
    #     primaryjoin="and_(Product.id==ProductTag.template_id, ProductTag.is_deleted==False)",
    #     secondaryjoin="and_(Tag.id==ProductTag.tag_id, Tag.is_deleted==False)",
    #     backref="products",
    #     lazy='selectin'
    # )
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(Product.id==foreign(TagAssociation.entity_id), TagAssociation.model_type==products, TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==TagAssociation.tag_id, Tag.is_deleted==False)",
        backref="products",
        lazy='selectin'
    )
    
    price = relationship(
        'ProductPrice',
        backref='products',
        uselist=False,
        primaryjoin='and_(ProductPrice.product_id==Product.id, ProductPrice.is_active==True)',
        lazy='selectin'
    )
    

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
        lazy='selectin'
    )
    

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
    
    is_active = sa.Column(sa.Boolean, server_default='true')  # Tiered pricing
    
    # Relationships
    product = relationship("Product")
    variant = relationship("ProductVariant")


# class ProductCategory(BaseTableModel):
#     __tablename__ = 'product_categories'
    
#     product_id = sa.Column(sa.String, sa.ForeignKey('products.id'), index=True, nullable=True)
#     category_id = sa.Column(sa.String, sa.ForeignKey('categories.id'), index=True, nullable=True)


# class ProductTag(BaseTableModel):
#     __tablename__ = 'product_tags'
    
#     product_id = sa.Column(sa.String, sa.ForeignKey('products.id'), index=True, nullable=True)
#     tag_id = sa.Column(sa.String, sa.ForeignKey('tags.id'), index=True, nullable=True)
