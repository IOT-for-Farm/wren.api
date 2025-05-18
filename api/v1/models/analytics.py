import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Analytics(BaseTableModel):
    __tablename__ = 'analytics'


