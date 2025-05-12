import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.content import ContentReviewStatus, ContentStatus, ContentType, ContentVisibility


# class ContentTag(BaseTableModel):
#     __tablename__ = 'content_tags'
    
#     content_id = sa.Column(sa.String, sa.ForeignKey("contents.id"), nullable=False)
#     tag_id = sa.Column(sa.String, sa.ForeignKey("tags.id"), nullable=False)
    
    
class Content(BaseTableModel):
    __tablename__ = 'contents'
    
    title = sa.Column(sa.String, nullable=False)
    body = sa.Column(sa.Text, nullable=True)  # HTML or markdown body
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), nullable=False)
    author_id = sa.Column(sa.String, sa.ForeignKey("users.id"), nullable=False)
    content_template_id = sa.Column(sa.String, sa.ForeignKey("content_templates.id"), nullable=True)
    content_type = sa.Column(sa.String, default=ContentType.ARTICLE.value)  # e.g., article, ad, page
    is_visible_on_website = sa.Column(sa.Boolean, server_default="true")
    visibility = sa.Column(sa.String, default=ContentVisibility.PUBLIC.value)  # public, private, unlisted
    cover_image_url = sa.Column(sa.String, nullable=True)
    content_url = sa.Column(sa.String, nullable=True)
    content_status = sa.Column(sa.String, default=ContentStatus.UNPUBLISHED.value)
    review_status = sa.Column(sa.String, default=ContentReviewStatus.PENDING.value)
    published_at = sa.Column(sa.DateTime, nullable=True)
    
    # For automated publishing
    publish_date = sa.Column(sa.DateTime, nullable=True)
    expiration_date = sa.Column(sa.DateTime, nullable=True)
    
    # For versioning
    current_version = sa.Column(sa.Integer, default=1)
    
    # SEO Support
    seo_title = sa.Column(sa.String, nullable=True)
    seo_description = sa.Column(sa.String, nullable=True)
    seo_keywords = sa.Column(sa.String, nullable=True)  # Comma-separated
    slug = sa.Column(sa.String, unique=True, index=True)
    
    # Additional info
    additional_info = sa.Column(sa.JSON, default={})

    organization = relationship("Organization", backref='organization_contents')
    author = relationship("User", backref='user_contents', lazy='selectin')
    versions = relationship("ContentVersion", back_populates="content", cascade="all, delete-orphan")
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(Content.id==foreign(TagAssociation.entity_id), "
                   "TagAssociation.model_type=='contents', "
                   "TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==foreign(TagAssociation.tag_id), "
                     "Tag.is_deleted==False)",
        backref="contents",
        lazy='selectin',
        viewonly=True
    )
    
    attachments = relationship(
        'File',
        primaryjoin='and_(Content.id==foreign(File.model_id), File.is_deleted==False)',
        lazy='selectin',
        backref='contents',
        viewonly=True
    )
    # analytics = relationship(
    #     "ContentAnalytics", 
    #     back_populates="content", 
    #     uselist=False, 
    #     cascade="all, delete-orphan"
    # )
    

class ContentVersion(BaseTableModel):
    __tablename__ = 'content_versions'
    
    content_id = sa.Column(sa.String, sa.ForeignKey("contents.id"), index=True)
    version = sa.Column(sa.Integer, nullable=False)
    
    title = sa.Column(sa.String, nullable=False)
    body = sa.Column(sa.Text, nullable=True)  # HTML or markdown body
    content_type = sa.Column(sa.String, default=ContentType.ARTICLE.value)  # e.g., article, ad, page
    is_visible_on_website = sa.Column(sa.Boolean, server_default="true")
    visibility = sa.Column(sa.String, default=ContentVisibility.PUBLIC.value)  # public, private, unlisted
    cover_image_url = sa.Column(sa.String, nullable=True)
    content_template_id = sa.Column(sa.String, sa.ForeignKey("content_templates.id"), nullable=True)
    author_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    
    content = relationship("Content", back_populates="versions")
    author = relationship("User", lazy="selectin")


class ContentAnalytics(BaseTableModel):
    __tablename__ = "content_analytics"

    content_id = sa.Column(sa.String, sa.ForeignKey("contents.id"), nullable=False, index=True)
    
    views = sa.Column(sa.Integer, default=0)
    clicks = sa.Column(sa.Integer, default=0)
    shares = sa.Column(sa.Integer, default=0)
    likes = sa.Column(sa.Integer, default=0)
    comments_count = sa.Column(sa.Integer, default=0)
    average_time_spent = sa.Column(sa.Float, default=0.0, doc="Time spent on content in seconds")

    device_type = sa.Column(sa.String, nullable=True, doc="e.g., mobile, desktop, tablet")
    user_location = sa.Column(sa.String, nullable=True, doc="City or Country if available")
    referrer_url = sa.Column(sa.String, nullable=True, doc="Where the user came from")

    # content = relationship("Content", back_populates="analytics")
    

class ContentTemplate(BaseTableModel):
    __tablename__ = "content_templates"

    name = sa.Column(sa.String, nullable=False, index=True)
    description = sa.Column(sa.Text, nullable=True)
    organization_id = sa.Column(sa.String, index=True, nullable=False)
    content_type = sa.Column(sa.String, index=True, default=ContentType.ARTICLE.value)  # Can reference your ContentType enum
    body = sa.Column(sa.Text, nullable=False)  # HTML or markdown body
    is_active = sa.Column(sa.Boolean, default=True)


class ContentTranslation(BaseTableModel):
    __tablename__ = "content_translations"

    content_id = sa.Column(sa.String, sa.ForeignKey("contents.id"), index=True)
    language_code = sa.Column(sa.String, nullable=False)  # e.g., 'en', 'fr', 'ha'
    title = sa.Column(sa.String, nullable=False)
    body = sa.Column(sa.Text)

    content = relationship("Content", backref="translations")


class ContentTarget(BaseTableModel):
    __tablename__ = "content_targets"

    content_id = sa.Column(sa.String, sa.ForeignKey("contents.id"), index=True)
    user_role = sa.Column(sa.String, nullable=True)
    country = sa.Column(sa.String, nullable=True)
    state = sa.Column(sa.String, nullable=True)
    gender = sa.Column(sa.String, nullable=True)
    age_group = sa.Column(sa.String, nullable=True)  # e.g., '18-25', '26-35'

    content = relationship("Content", backref="targets")
    

class ContentPromotion(BaseTableModel):
    __tablename__ = "content_promotions"

    content_id = sa.Column(sa.String, sa.ForeignKey("contents.id"), index=True)
    start_date = sa.Column(sa.DateTime, nullable=False)
    end_date = sa.Column(sa.DateTime, nullable=False)
    budget = sa.Column(sa.Float, nullable=True)  # Optional ad spend
    platform = sa.Column(sa.String, nullable=True)  # e.g., 'website', 'newsletter', 'facebook'
    is_active = sa.Column(sa.Boolean, default=True)

    content = relationship("Content", backref="promotions")
