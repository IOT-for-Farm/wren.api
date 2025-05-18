import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class ActivityLog(BaseTableModel):
    __tablename__ = "activity_logs"

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"), nullable=True)

    model_name = sa.Column(sa.String)
    model_id = sa.Column(sa.String)  # ID of the affected record
    action = sa.Column(sa.String)  # e.g. 'CREATE', 'UPDATE', 'DELETE'
    description = sa.Column(sa.Text)  # what changed?
    timestamp = sa.Column(sa.DateTime, server_default=sa.func.now())

    organization = relationship("Organization")
    user = relationship("User")