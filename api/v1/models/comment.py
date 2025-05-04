import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session, backref
from sqlalchemy.ext.hybrid import hybrid_method

from api.core.base.base_model import BaseTableModel


class Comment(BaseTableModel):
    __tablename__ = 'comments'
    
    model_name = sa.Column(sa.String, index=True) 
    model_id = sa.Column(sa.String, index=True)
    commenter_id = sa.Column(sa.String, sa.ForeignKey("users.id"), index=True)
    parent_id = sa.Column(sa.String, sa.ForeignKey("comments.id", ondelete="cascade"))
    
    email = sa.Column(sa.String)
    name = sa.Column(sa.String)
    text = sa.Column(sa.Text, nullable=False)
    
    downvotes = sa.Column(sa.Integer, default=0, nullable=False)
    upvotes = sa.Column(sa.Integer, default=0, nullable=False)
    
    parent = relationship(
        "Comment", 
        backref=backref('replies',  cascade="all, delete-orphan"), 
        remote_side='Comment.id', 
        post_update=True, 
        single_parent=True, 
        uselist=True
    )
   
    commenter = relationship("User", viewonly=True, backref="comments", foreign_keys=[commenter_id])

    @hybrid_method
    def upvote(self):
        self.upvotes += 1
    
    @hybrid_method
    def downvote(self):
        self.downvotes += 1



