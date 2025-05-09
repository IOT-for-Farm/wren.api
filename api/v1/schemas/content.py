from fastapi import Form, File, UploadFile
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from enum import Enum
from datetime import date, datetime


class ContentType(str, Enum):
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    ANNOUNCEMENT = "announcement"
    ADVERTISEMENT = "advertisement"
    LANDING_PAGE = "landing_page"
    PRESS_RELEASE = "press_release"
    CASE_STUDY = "case_study"
    WHITE_PAPER = "white_paper"
    PRODUCT_UPDATE = "product_update"
    VIDEO = "video"
    PODCAST = "podcast"
    TESTIMONIAL = "testimonial"
    FAQ = "faq"
    KNOWLEDGE_BASE = "knowledge_base"
    EVENT = "event"
    JOB_POST = "job_post"
    NEWS = "news"
    WEBINAR = "webinar"
    

class ContentVisibility(str, Enum):
    PUBLIC = "public"       # Visible to everyone
    PRIVATE = "private"     # Only accessible internally
    UNLISTED = "unlisted"   # Accessible via link but not publicly listed
    

class ContentStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    

class ContentReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    

class ContentBase(BaseModel):
    unique_id: Optional[str] = Form(None)
    cover_image: Optional[UploadFile] = File(None)
    attachments: Optional[List[UploadFile]] = File(None)
    
    title: str = Form(...)
    body: Optional[str] = Form(None)
    content_type: Optional[ContentType] = Form(ContentType.ARTICLE)
    # content_status: Optional[ContentStatus] = Form(ContentStatus.UNPUBLISHED)
    # review_status: Optional[ContentReviewStatus] = Form(ContentReviewStatus.PENDING)
    is_visible_on_website: Optional[bool] = Form(True)
    visibility: Optional[ContentVisibility] = Form(ContentVisibility.PUBLIC)
    cover_image_url: Optional[str] = Form(None)
    tag_ids: Optional[str] = Form(None)
    content_template_id: Optional[str] = Form(None)
    website_base_url: Optional[str] = Form(None)
    
    publish_date: Optional[datetime] = Form(None)
    expiration_date: Optional[datetime] = Form(None)
    
    seo_title: Optional[str] = Form(None)
    seo_description: Optional[str] = Form(None)
    seo_keywords: Optional[str] = Form(None)
    slug: Optional[str] = Form(None)
    
    # additional_info: Optional[str] = Form(None)

    class Config:
        from_attributes = True


class ContentCreate(ContentBase):
    organization_id: str = Form(...)
    
    @field_validator("publish_date")
    def validate_publish_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Publish date cannot be in the past.")
        return v

    @field_validator("expiration_date")
    def validate_expiration_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Expiration date cannot be in the past.")
        return v
    
    @model_validator(mode="after")
    def validate_date_range(self):
        if self.publish_date and self.expiration_date:
            if self.expiration_date < self.publish_date:
                raise ValueError("Expiration date cannot be before publish date.")
        return self


class ContentUpdate(BaseModel):
    cover_image: Optional[UploadFile] = File(None)
    attachments: Optional[List[UploadFile]] = File(None)
    
    title: Optional[str] = Form(None)
    body: Optional[str] = Form(None)
    content_type: Optional[ContentType] = Form(None)
    is_visible_on_website: Optional[bool] = Form(None)
    visibility: Optional[ContentVisibility] = Form(None)
    cover_image_url: Optional[str] = Form(None)
    tag_ids: Optional[str] = Form(None)
    content_status: Optional[ContentStatus] = Form(None)
    review_status: Optional[ContentReviewStatus] = Form(None)
    content_template_id: Optional[str] = Form(None)
    
    publish_date: Optional[datetime] = Form(None)
    expiration_date: Optional[datetime] = Form(None)
    
    seo_title: Optional[str] = Form(None)
    seo_description: Optional[str] = Form(None)
    seo_keywords: Optional[str] = Form(None)
    
    # additional_info: Optional[str] = Form(None)
    
    @field_validator("publish_date")
    def validate_publish_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Publish date cannot be in the past.")
        return v

    @field_validator("expiration_date")
    def validate_expiration_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Expiration date cannot be in the past.")
        return v
    
    @model_validator(mode="after")
    def validate_date_range(self):
        if self.publish_date and self.expiration_date:
            if self.expiration_date < self.publish_date:
                raise ValueError("Expiration date cannot be before publish date.")
        return self

    class Config:
        from_attributes = True


class ContentAnalyticsBase(BaseModel):
    views: Optional[int] = 0
    clicks: Optional[int] = 0
    shares: Optional[int] = 0
    likes: Optional[int] = 0
    comments_count: Optional[int] = 0
    average_time_spent: Optional[float] = 0.0
    device_type: Optional[str] = Field(None, description="e.g., mobile, desktop, tablet")
    user_location: Optional[str] = Field(None, description="City or Country")
    referrer_url: Optional[str] = Field(None, description="Where the user came from")


class CreateContentAnalytics(ContentAnalyticsBase):
    content_id: str


class UpdateContentAnalytics(BaseModel):
    views: Optional[int] = None
    clicks: Optional[int] = None
    shares: Optional[int] = None
    likes: Optional[int] = None
    comments_count: Optional[int] = None
    average_time_spent: Optional[float] = None
    device_type: Optional[str] = None
    user_location: Optional[str] = None
    referrer_url: Optional[str] = None


class ContentTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    content_type: ContentType
    body: str
    is_active: Optional[bool] = True
    organization_id: str
    

class UpdateContentTemplate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content_type: Optional[ContentType] = None
    body: Optional[str] = None
    is_active: Optional[bool] = None


class ContentTargetBase(BaseModel):
    user_role: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    

class ContentPromotionBase(BaseModel):
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = None
    platform: Optional[str] = None
    is_active: Optional[bool] = True
    

class ContentTranslationBase(BaseModel):
    language_code: str  # 'en', 'fr', 'ha', etc.
    title: str
    body: Optional[str] = None
