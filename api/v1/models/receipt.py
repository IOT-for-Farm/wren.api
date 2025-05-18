import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class Receipt(BaseTableModel):
    __tablename__ = 'receipts'
    
    invoice_id = sa.Column(sa.String, sa.ForeignKey("invoices.id"), index=True)
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    customer_id = sa.Column(sa.String, sa.ForeignKey("business_partners.id"), index=True)
    vendor_id = sa.Column(sa.String, sa.ForeignKey("business_partners.id"), index=True)
    order_id = sa.Column(sa.String, sa.ForeignKey("orders.id"), index=True)
    amount = sa.Column(sa.Numeric(12, 2))
    payment_date = sa.Column(sa.DateTime, default=sa.func.now())
    payment_method = sa.Column(sa.String, index=True)
    transaction_reference = sa.Column(sa.String)
    
    # invoice = relationship("Invoice", back_populates="receipt", uselist=False)
