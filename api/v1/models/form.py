import sqlalchemy as sa
from sqlalchemy.orm import relationship

from api.core.base.base_model import BaseTableModel


class FormTemplate(BaseTableModel):
    __tablename__ = 'form_templates'

    organization_id = sa.Column(sa.String, index=True)
    # user_id = sa.Column(sa.String, sa.ForeignKey('users.id'), nullable=True)
    template_name = sa.Column(sa.String, nullable=False)
    purpose = sa.Column(sa.String, nullable=True)
    fields = sa.Column(sa.JSON)  # contains the form fields. Should contain label, type eg text, textarea, number, email and all other html field types
    
    # tags = relationship(
    #     "Tag",
    #     secondary='form_template_tags',
    #     primaryjoin="and_(FormTemplate.id==FormTemplateTag.form_template_id, FormTemplateTag.is_deleted==False)",
    #     secondaryjoin="and_(Tag.id==FormTemplateTag.tag_id, Tag.is_deleted==False)",
    #     backref="form_templates",
    #     viewonly=True,
    #     lazy='selectin'
    # )
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(FormTemplate.id==foreign(TagAssociation.entity_id), TagAssociation.model_type==form_templates, TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==TagAssociation.tag_id, Tag.is_deleted==False)",
        backref="form_templates",
        lazy='selectin'
    )
    
    
class Form(BaseTableModel):
    __tablename__ = 'forms'

    organization_id = sa.Column(sa.String, sa.ForeignKey('organizations.id'), index=True)
    form_template_id = sa.Column(sa.String, sa.ForeignKey('form_templates.id'), index=True, nullable=True)
    form_name = sa.Column(sa.String, nullable=False)
    slug = sa.Column(sa.String, nullable=True, index=True, unique=True)
    purpose = sa.Column(sa.String, nullable=True)
    url = sa.Column(sa.String, nullable=True)  # default will be generated if none is
    fields = sa.Column(sa.JSON)  # contains the form fields. Should contain label, type eg text, textarea, number, email and all other html field types
    is_active = sa.Column(sa.Boolean, server_default='true')
    receive_response_email_notifications = sa.Column(sa.Boolean, server_default='false')
    allow_more_than_one_user_submission = sa.Column(sa.Boolean, server_default='false')
    
    responses = relationship('FormResponse', back_populates='form')
    form_template = relationship(
        'FormTemplate',
        uselist=False,
        lazy='selectin',
        backref="forms",
        primaryjoin="and_(FormTemplate.id==Form.form_template_id, FormTemplate.is_deleted==False)",
    )
    

class FormResponse(BaseTableModel):
    __tablename__ = 'form_responses'
    
    form_id = sa.Column(sa.String, sa.ForeignKey('forms.id'), nullable=True)
    email = sa.Column(sa.String, nullable=True)  # email of the user who filled the form
    data = sa.Column(sa.JSON)  # can contain form responses for forms created. Should contain label, type, and response
    status = sa.Column(sa.String, default='draft')
    send_email_to_respondent = sa.Column(sa.Boolean, server_default='false')
    
    form = relationship('Form', back_populates='responses')


# class FormTemplateTag(BaseTableModel):
#     __tablename__ = "form_template_tags"
    
#     form_template_id = sa.Column(sa.String, sa.ForeignKey("form_templates.id"), nullable=False)
#     tag_id = sa.Column(sa.String, sa.ForeignKey("tags.id"), nullable=False)
