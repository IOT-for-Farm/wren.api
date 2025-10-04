import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session, validates
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel
from api.db.database import get_db_with_ctx_manager

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
        lazy="selectin",
        viewonly=True
    )
    locations = relationship(
        'Location', 
        primaryjoin="and_(Organization.id == foreign(Location.model_id), Location.is_deleted == False)",
        backref="organization_locations",
        lazy="selectin",
        viewonly=True
    )
    roles = relationship(
        "OrganizationRole", 
        backref="organization",
        primaryjoin="and_(Organization.id == foreign(OrganizationRole.organization_id), OrganizationRole.is_deleted == False)",  # add Organization.id=='-1' for default roles to show
        lazy="selectin"
    )
    
    @hybrid_property
    def member_count(self):
        with get_db_with_ctx_manager() as db:
            _, _, count = OrganizationMember.fetch_by_field(
                db=db, paginate=False,
                organization_id=self.id
            )
            
            return count
    
    def to_dict(self, excludes = []):
        return {
            "member_count": self.member_count,
            **super().to_dict(excludes),
            # "creator": self.creator.to_dict()
        }
    

class OrganizationMember(BaseTableModel):
    __tablename__ = "organization_members"
    
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"))
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    role_id = sa.Column(sa.String, sa.ForeignKey("organization_roles.id"))
    
    # Member Details
    title = sa.Column(sa.String(100))
    join_date = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    is_primary_contact = sa.Column(sa.Boolean, default=False)
    is_active = sa.Column(sa.Boolean, default=True)
    
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
    # organization = relationship("Organization", backref="org_roles")
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


class OrganizationSecret(BaseTableModel):
    __tablename__ = "organization_secrets"
    
    organization_id = sa.Column(sa.String, sa.ForeignKey('organizations.id'), nullable=False)
    key = sa.Column(sa.String, nullable=False)
    value = sa.Column(sa.Text, nullable=False)
