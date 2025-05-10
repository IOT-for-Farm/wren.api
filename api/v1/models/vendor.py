import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel
from api.v1.models.business_partner import BusinessPartner
from api.v1.schemas.vendor import VendorType


# class VendorTag(BaseTableModel):
#     __tablename__ = 'vendor_tags'
    
#     vendor_id = sa.Column(sa.String, sa.ForeignKey("vendors.id"), nullable=False)
#     tag_id = sa.Column(sa.String, sa.ForeignKey("tags.id"), nullable=False)
    

class Vendor(BusinessPartner):
    __tablename__ = 'vendors'
    
    business_partner_id = sa.Column(
        sa.String, 
        sa.ForeignKey('business_partners.id'),
        primary_key=True,
        nullable=False, index=True
    )
    
    vendor_type = sa.Column(sa.String, default=VendorType.retailer.value)

    contact_person_name = sa.Column(sa.String, nullable=True)
    contact_person_email = sa.Column(sa.String, nullable=True)
    contact_person_phone = sa.Column(sa.String, nullable=True)
    contact_person_phone_country_code = sa.Column(sa.String, nullable=True)
    
    payment_terms = sa.Column(sa.String, nullable=True)  # prepaid, commission
    commission_percentage = sa.Column(sa.Float, nullable=True)
    
    business_partner = relationship(
        'BusinessPartner',
        lazy='selectin',
        backref='vendor',
        uselist=False
    )
    
    # tags = relationship(
    #     "Tag",
    #     secondary='vendor_tags',
    #     primaryjoin="and_(Vendor.id==VendorTag.vendor_id, VendorTag.is_deleted==False)",
    #     secondaryjoin="and_(Tag.id==VendorTag.tag_id, Tag.is_deleted==False)",
    #     backref="vendors",
    #     lazy='selectin'
    # )
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(Vendor.id==foreign(TagAssociation.entity_id), TagAssociation.model_type==vendors, TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==TagAssociation.tag_id, Tag.is_deleted==False)",
        backref="vendors",
        lazy='selectin'
    )
    
    photos = relationship(
        'File',
        backref='vendor_photos',
        # primaryjoin='and_(Vendor.id == foreign(File.model_id), File.is_deleted == False, Vendor.organization_id==File.organization_id)',
        primaryjoin='and_(Vendor.id == foreign(File.model_id), File.is_deleted == False)',
        lazy='selectin'
    )
    
    categories = relationship(
        'Category',
        secondary='category_association',
        primaryjoin='and_(CategoryAssociation.product_id==Vendor.id, CategoryAssociation.is_deleted==False, CategoryAssociation.model_type==vendors)',
        secondaryjoin='and_(Category.id==CategoryAssociation.category_id, Category.is_deleted==False)',
        lazy='selectin',
        backref='vendors'
    )
    
    accounts = relationship(
        'Account',
        primaryjoin='and_(Vendor.id==foreign(Account.owner_id), Account.is_deleted==False)',
        backref='vendor_accounts',
        lazy='selectin',
    )
