import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


# class TemplateTag(BaseTableModel):
#     __tablename__ = 'template_tags'
    
#     template_id = sa.Column(sa.String, sa.ForeignKey("templates.id"), nullable=False)
#     tag_id = sa.Column(sa.String, sa.ForeignKey("tags.id"), nullable=False)


class Template(BaseTableModel):
    __tablename__ = "templates"

    name = sa.Column(sa.String(128), nullable=False, index=True)
    body = sa.Column(sa.Text(), nullable=False)
    subject = sa.Column(sa.String(255), nullable=True)
    image_url = sa.Column(sa.String(255), nullable=True)
    footer = sa.Column(sa.String(512), nullable=True)
    description = sa.Column(sa.String(512), nullable=True)
    is_active = sa.Column(sa.Boolean, default=True)
    organization_id = sa.Column(sa.String(255), nullable=False, index=True)
    layout_id = sa.Column(sa.String, sa.ForeignKey("template_layouts.id"), default=None, index=True)
    feature = sa.Column(sa.String(191), nullable=True, index=True)  # should be nullable
    
    tags = relationship(
        "Tag",
        secondary='tag_association',
        primaryjoin="and_(Template.id==foreign(TagAssociation.entity_id), "
                   "TagAssociation.model_type=='templates', "
                   "TagAssociation.is_deleted==False)",
        secondaryjoin="and_(Tag.id==foreign(TagAssociation.tag_id), "
                     "Tag.is_deleted==False)",
        backref="templates",
        lazy='selectin',
        viewonly=True
    )
    
    layout = relationship(
        "Layout",
        backref="templates",
        uselist=False,
        primaryjoin="and_(Layout.id==Template.layout_id, Layout.is_deleted==False)",
        lazy='selectin'
    )
