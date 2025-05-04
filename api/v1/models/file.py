import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property                      

from api.core.base.base_model import BaseTableModel


class File(BaseTableModel):
    __tablename__ = 'files'
    
    organization_id = sa.Column(sa.String, sa.ForeignKey('organizations.id'), index=True)
    file_name = sa.Column(sa.String(255), nullable=False, index=True)
    file_path = sa.Column(sa.String(1000), nullable=False, index=True)
    file_size = sa.Column(sa.Integer)
    model_id = sa.Column(sa.String, nullable=False, index=True)
    model_name = sa.Column(sa.String(255), nullable=False, index=True)
    url = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text)
    content = sa.Column(sa.Text)
    label = sa.Column(sa.String)


class Folder(BaseTableModel):
    __tablename__ = 'folders'
    
    name = sa.Column(sa.String, nullable=False)
    slug = sa.Column(sa.String, nullable=True, index=True, unique=True)
    
    parent_id = sa.Column(sa.String, sa.ForeignKey('folders.id', ondelete="cascade"), nullable=True, index=True)
    organization_id = sa.Column(sa.String, sa.ForeignKey('organizations.id'), index=True)
    
    # files = relationship(
    #     'File',
    #     backref='file_folder',
    #     primaryjoin='and_(Folder.id == foreign(File.model_id), File.is_deleted == False)',
    #     lazy='selectin'
    # )
    
    # parent = relationship(
    #     "Folder", 
    #     remote_side='Folder.id', 
    #     uselist=False, 
    #     foreign_keys=[parent_id],
    #     lazy='selectin',
    #     backref=backref('sub_folders',  cascade="all, delete-orphan"), 
    #     # post_update=True, 
    #     # single_parent=True, 
    # )
    
    # child_folders = relationship(
    #     "Folder", 
    #     overlaps='parent', 
    #     lazy='selectin'
    # )
    
    # @hybrid_property
    # def folder_size(self):
        
