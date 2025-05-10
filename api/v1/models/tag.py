import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Tag(BaseTableModel):
    __tablename__ = 'tags'

    name = sa.Column(sa.String, nullable=False, index=True)
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), nullable=True, index=True)
    model_type = sa.Column(sa.String, nullable=False, index=True)
    group = sa.Column(sa.String, nullable=True, index=True)
    parent_id = sa.Column(sa.String, index=True, nullable=True)


class TagAssociation(BaseTableModel):
    __tablename__ = "tag_association"
    
    entity_id = sa.Column(sa.String, nullable=False, index=True)
    model_type = sa.Column(sa.String, nullable=False, index=True)
    tag_id = sa.Column(sa.String, sa.ForeignKey('tags.id'), nullable=False, index=True)

    tag = relationship("Tag", backref="tag_assoc")
    