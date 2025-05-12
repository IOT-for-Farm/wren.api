import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Review(BaseTableModel):
    __tablename__ = 'reviews'

    # customer_id = sa.Column(sa.String, nullable=True)
    model_id = sa.Column(sa.String, nullable=False, index=True)
    model_type = sa.Column(sa.String, nullable=False, index=True)
    name = sa.Column(sa.String, nullable=False)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)
    email = sa.Column(sa.String, nullable=False)
    title = sa.Column(sa.String, nullable=True)
    comment = sa.Column(sa.Text, nullable=True)
    star_rating = sa.Column(sa.Integer, sa.CheckConstraint("star_rating <= 5"))
    is_published = sa.Column(sa.Boolean, server_default='false', index=True)
    published_at = sa.Column(sa.DateTime, default=None)
