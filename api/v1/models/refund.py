import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Refund(BaseTableModel):
    __tablename__ = 'refunds'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    payment_id = sa.Column(sa.String, sa.ForeignKey("payments.id"), index=True)
    amount = sa.Column(sa.Numeric(12, 2))
    reason = sa.Column(sa.String)
    status = sa.Column(sa.String, default="pending", index=True)
    refund_date = sa.Column(sa.DateTime)
    
    payment = relationship('Payment', back_populates='refunds')
