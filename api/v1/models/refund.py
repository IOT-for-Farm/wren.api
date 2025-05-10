import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Refund(BaseTableModel):
    __tablename__ = 'refunds'

    payment_id = sa.Column(sa.String, sa.ForeignKey("payments.id"))
    amount = sa.Column(sa.Numeric(12, 2))
    reason = sa.Column(sa.String)
    status = sa.Column(sa.String, default="pending")
    refund_date = sa.Column(sa.DateTime, default=sa.func.now())
