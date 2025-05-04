import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session, validates

from api.core.base.base_model import BaseTableModel


class ContactInfo(BaseTableModel):
    __tablename__ = "contact_infos"
    
    model_name = sa.Column(sa.String, nullable=False, index=True)
    model_id = sa.Column(sa.String, nullable=False, index=True)
    contact_type = sa.Column(sa.String, nullable=False, index=True)  # email or phone
    contact_data = sa.Column(sa.String, nullable=False)
    phone_country_code = sa.Column(sa.String)
    is_primary = sa.Column(sa.Boolean, server_default="false")
