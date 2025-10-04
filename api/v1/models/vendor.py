import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel
from api.v1.models.business_partner import BusinessPartner
from api.v1.schemas.vendor import VendorType


class Vendor(BaseTableModel):
    __tablename__ = 'vendors'
    
    id = None
    
    business_partner_id = sa.Column(
        sa.String, 
        sa.ForeignKey('business_partners.id'),
        primary_key=True,
        nullable=False, index=True
    )  # primary key for this model
    
    organization_id = sa.Column(sa.String, sa.ForeignKey('organizations.id'), index=True)
    
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
        uselist=False,
        viewonly=True
    )
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(Vendor.business_partner_id==foreign(TagAssociation.entity_id), "
                   "TagAssociation.model_type=='vendors', "
                   "TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==foreign(TagAssociation.tag_id), "
                     "Tag.is_deleted==False)",
        backref="vendors",
        lazy='selectin',
        viewonly=True
    )
    
    photos = relationship(
        'File',
        backref='vendor_photos',
        # primaryjoin='and_(Vendor.id == foreign(File.model_id), File.is_deleted == False, Vendor.organization_id==File.organization_id)',
        primaryjoin='and_(Vendor.business_partner_id == foreign(File.model_id), File.is_deleted == False, Vendor.organization_id==File.organization_id)',
        lazy='selectin',
        viewonly=True
    )
    
    categories = relationship(
        'Category',
        secondary='category_association',
        primaryjoin='and_(foreign(CategoryAssociation.entity_id)==Vendor.business_partner_id, '
                   'CategoryAssociation.is_deleted==False, '
                   'CategoryAssociation.model_type=="vendors")',
        secondaryjoin='and_(Category.id==foreign(CategoryAssociation.category_id), '
                     'Category.is_deleted==False)',
        lazy='selectin',
        backref='vendors',
        viewonly=True
    )
    
    accounts = relationship(
        'Account',
        primaryjoin='and_(Vendor.business_partner_id==foreign(Account.owner_id), Account.is_deleted==False)',
        backref='vendor_accounts',
        lazy='selectin',
        viewonly=True
    )
