import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session, backref

from api.core.base.base_model import BaseTableModel


class Category(BaseTableModel):
    __tablename__ = 'categories'
    
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    slug = sa.Column(sa.String, nullable=True, index=True, unique=True)
    
    parent_id = sa.Column(sa.String, sa.ForeignKey('categories.id', ondelete="cascade"), nullable=True, index=True)
    organization_id = sa.Column(sa.String, sa.ForeignKey('organizations.id'), index=True)
    
    photos = relationship(
        'File',
        backref='category_files',
        primaryjoin='and_(Category.id == foreign(File.model_id), File.is_deleted == False)',
        lazy='selectin'
    )
    
    parent = relationship(
        "Category", 
        remote_side='Category.id', 
        uselist=False, 
        foreign_keys=[parent_id],
        lazy='selectin',
        backref=backref('sub_categories',  cascade="all, delete-orphan"), 
        post_update=True, 
        single_parent=True, 
    )
    
    # children = relationship(
    #     "Category", 
    #     overlaps='parent', 
    #     # lazy='selectin'
    # )


