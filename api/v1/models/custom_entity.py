import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Custom_entity(BaseTableModel):
    __tablename__ = 'custom_entitys'


