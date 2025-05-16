import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.email import EmailStatus


class EmailRegistry(BaseTableModel):
    __tablename__ = 'email_registry'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), nullable=False, index=True)
    
    recipients = sa.Column(sa.JSON, default=[])
    subject = sa.Column(sa.String, nullable=True)
    body = sa.Column(sa.Text, nullable=True)
    footer = sa.Column(sa.Text, nullable=True)
        
    status = sa.Column(sa.String, default=EmailStatus.PENDING.value, index=True)
    priority = sa.Column(sa.Integer, default=1, index=True)
    retries = sa.Column(sa.Integer, default=0)
    date_sent = sa.Column(sa.DateTime, nullable=True)
    
    context = sa.Column(sa.JSON, default={})
    template_id = sa.Column(sa.String, sa.ForeignKey('templates.id'))
    layout_id = sa.Column(sa.String, sa.ForeignKey('template_layouts.id'))
    
    template = relationship(
        'Template',
        backref='email_registry',
        uselist=False,
        lazy='selectin'
    )
    
    layout = relationship(
        'Layout',
        backref='email_registry',
        uselist=False,
        lazy='selectin'
    )
    
    attachments = relationship(
        'File',
        primaryjoin='and_(EmailRegistry.id==foreign(File.model_id), File.is_deleted==False, File.organization_id==EmailRegistry.organization_id)',
        lazy='selectin',
        backref='email_attachments',
        viewonly=True
    )
