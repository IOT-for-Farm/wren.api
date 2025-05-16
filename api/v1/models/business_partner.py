import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session, backref
from sqlalchemy.ext.hybrid import hybrid_method

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.business_partner import BusinessPartnerType


class BusinessPartner(BaseTableModel):
    __tablename__ = 'business_partners'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), nullable=False)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    
    partner_type = sa.Column(sa.String, default=BusinessPartnerType.vendor.value)  # vendor/customer
    slug = sa.Column(sa.String, unique=True, index=True)

    # Contact & Identity
    first_name = sa.Column(sa.String, nullable=False)
    last_name = sa.Column(sa.String, nullable=False)
    phone = sa.Column(sa.String, nullable=True)
    phone_country_code = sa.Column(sa.String, nullable=True)
    image_url = sa.Column(sa.String)
    
    # For auth purposes
    email = sa.Column(sa.String, nullable=False, index=True)
    password = sa.Column(sa.String, nullable=True)

    # Business Info
    company_name = sa.Column(sa.String, nullable=True)

    # Metadata
    is_active = sa.Column(sa.Boolean, server_default='true')

    # Extensibility
    additional_info = sa.Column(sa.JSON, default={})
    notes = sa.Column(sa.Text, nullable=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")
    
    contact_infos = relationship(
        'ContactInfo', 
        primaryjoin="and_(BusinessPartner.id == foreign(ContactInfo.model_id), ContactInfo.is_deleted == False)",
        backref="business_partner_contact_infos",
        lazy="selectin",
        viewonly=True
    )
    
    locations = relationship(
        'Location', 
        primaryjoin="and_(BusinessPartner.id == foreign(Location.model_id), Location.is_deleted == False)",
        backref="business_partner_locations",
        lazy="selectin",
        viewonly=True
    )
    
    __table_args__ = (
        sa.UniqueConstraint("organization_id", "email", name="uq_email_organization"),
        # sa.UniqueConstraint("organization_id", "phone", "phone_country_code", name="uq_phone_organization"),
    )
    
    def to_dict(self, excludes = ...):
        return super().to_dict(excludes=['password'])
