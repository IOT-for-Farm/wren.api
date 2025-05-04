import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session, validates

from api.core.base.base_model import BaseTableModel

class Organization(BaseTableModel):
    __tablename__ = "organizations"
    
    name = sa.Column(sa.String(150), nullable=False)
    slug = sa.Column(sa.String, unique=True, nullable=False, index=True)  # URL-friendly identifier
    description = sa.Column(sa.Text)
    logo_url = sa.Column(sa.String(500))
    
    website = sa.Column(sa.String(255))
    social_media_links = sa.Column(sa.JSON)
    policy = sa.Column(sa.Text)
    terms_and_conditions = sa.Column(sa.Text)
    mission = sa.Column(sa.Text)
    vision = sa.Column(sa.Text)
    initials = sa.Column(sa.String(5))
    business_type = sa.Column(sa.String(225), default="retail")
    tagline = sa.Column(sa.Text)
    
    timezone = sa.Column(sa.String(50), default="UTC")
    currency = sa.Column(sa.String(10), default="NGN")
    
    created_by = sa.Column(sa.String, sa.ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", backref="organizations_created", lazy="selectin")
    contact_infos = relationship(
        'ContactInfo', 
        primaryjoin="and_(Organization.id == foreign(ContactInfo.model_id), ContactInfo.is_deleted == False)",
        backref="organization_contact_infos",
        lazy="selectin"
    )
    locations = relationship(
        'Location', 
        primaryjoin="and_(Organization.id == foreign(Location.model_id), Location.is_deleted == False)",
        backref="organization_locations",
        lazy="selectin"
    )
    roles = relationship(
        "OrganizationRole", 
        backref="organization",
        primaryjoin="and_(Organization.id == foreign(OrganizationRole.organization_id), OrganizationRole.is_deleted == False)",  # add Organization.id=='-1' for default roles to show
        lazy="selectin"
    )
    # members = relationship(
    #     "User",
    #     primaryjoin="User.id == foreign(OrganizationMember.user_id)",
    #     backref="user_members", 
    #     lazy='selectin'
    # )
    # departments = relationship("Department", back_populates="organization")
    # billing = relationship("BillingAccount", back_populates="organization")
    # custom_fields = relationship("OrganizationCustomField", back_populates="organization")
    

class OrganizationMember(BaseTableModel):
    __tablename__ = "organization_members"
    
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"))
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    role_id = sa.Column(sa.String, sa.ForeignKey("organization_roles.id"))
    
    # Member Details
    title = sa.Column(sa.String(100))
    join_date = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    is_primary_contact = sa.Column(sa.Boolean, server_default='false')
    is_active = sa.Column(sa.Boolean, server_default='true')
    
    # Relationships
    user = relationship("User", backref='organizations', uselist=False, lazy='selectin')
    role = relationship(
        "OrganizationRole",
        # primaryjoin="and_(OrganizationMember.role_id == foreign(OrganizationRole.id))",
        backref="user_org_role", 
        lazy="selectin", 
        uselist=False
    )


class OrganizationRole(BaseTableModel):
    __tablename__ = "organization_roles"
    
    organization_id = sa.Column(sa.String)
    role_name = sa.Column(sa.String(50), nullable=False)
    permissions = sa.Column(sa.JSON)  # Flexible storage for permissions
    
    # Relationships
    # organization = relationship("Organization", backref="org_roles", lazy="selectin")
    # members = relationship("OrganizationMember", back_populates="role")


class OrganizationInvite(BaseTableModel):
    __tablename__ = "organization_invites"
    
    email = sa.Column(sa.String, index=True, nullable=False)
    role_id = sa.Column(sa.String, sa.ForeignKey('organization_roles.id'), index=True, nullable=False)
    inviter_id = sa.Column(sa.String, sa.ForeignKey("users.id"), index=True, nullable=False)
    organization_id = sa.Column(sa.String, sa.ForeignKey('organizations.id'), index=True, nullable=False)
    status = sa.Column(sa.String, default='pending', index=True, nullable=False)  # pending/accepted/revoked/declined
    invite_token = sa.Column(sa.String, index=True, nullable=False)
    
    # organization = relationship("Organization", backref="organization_invites", lazy="selectin", uselist=False)
    role = relationship("OrganizationRole", backref="org_invite_role", lazy="selectin", uselist=False)
    invited_by = relationship("User", backref="organization_invites", lazy="selectin", uselist=False)
    
    def to_dict(self, excludes = ...):
        return super().to_dict(excludes=['invite_token'])

# class OrganizationCustomField(BaseTableModel):
#     __tablename__ = "organization_custom_fields"
    
#     organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"))
#     field_name = sa.Column(sa.String(50), nullable=False)
#     field_type = sa.Column(sa.ENUM(
#         'text', 'number', 'date', 'boolean', 'dropdown', 
#         name="custom_field_type"
#     ), nullable=False)
#     field_value = sa.Column(sa.JSON)  # Flexible storage based on type
#     is_required = sa.Column(sa.Boolean, server_default='false')
    
#     # Relationships
#     organization = relationship("Organization", back_populates="custom_fields")
