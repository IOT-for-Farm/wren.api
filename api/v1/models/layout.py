import sqlalchemy as sa

from api.core.base.base_model import BaseTableModel


class Layout(BaseTableModel):
    __tablename__ = 'template_layouts'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True, nullable=False)
    name = sa.Column(sa.String(128), nullable=False, index=True)
    layout = sa.Column(sa.Text, nullable=False)
    feature = sa.Column(sa.String(191), nullable=True, index=True)  # should be nullable
