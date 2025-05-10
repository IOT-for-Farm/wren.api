import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Payment(BaseTableModel):
    __tablename__ = 'payments'

    invoice_id = sa.Column(sa.String, sa.ForeignKey("invoices.id"))
    amount = sa.Column(sa.Numeric(12, 2), nullable=False)
    payment_date = sa.Column(sa.DateTime, default=sa.func.now)
    method = sa.Column(sa.String, default='cash')  # e.g. "bank_transfer", "card", "cash"
    narration = sa.Column(sa.String, nullable=True)
    status = sa.Column(sa.String, default="pending")

    invoice = relationship("Invoice", back_populates="payments")