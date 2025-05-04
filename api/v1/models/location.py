import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Location(BaseTableModel):
    __tablename__ = 'locations'
    
    model_name = sa.Column(sa.String, nullable=True, index=True)
    model_id = sa.Column(sa.String, nullable=True, index=True)
    address = sa.Column(sa.Text)
    city = sa.Column(sa.String(50), index=True)
    state = sa.Column(sa.String(50), index=True)
    postal_code = sa.Column(sa.String(20), index=True)
    country = sa.Column(sa.String(50), index=True)
