from enum import Enum
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel


class LocationType(str, Enum):
    continent = 'continent'
    country = 'country'
    state = 'state'
    city = 'city'
    area = 'area'
    street = 'street'
    

class BaseLocation(BaseTableModel):
    __tablename__ = "base_locations"
    
    location_name = sa.Column(sa.String, nullable=False)
    location_type = sa.Column(sa.String, nullable=False)
    
    parent_id = sa.Column(sa.String, sa.ForeignKey('base_locations.id'), nullable=True)
    parent_name = sa.Column(sa.String, nullable=True)  # eg, Nigeria, Lagos, USA
    parent_type = sa.Column(sa.String, nullable=True)  # uses LocationType as well
    
    description = sa.Column(sa.Text)
    longitude = sa.Column(sa.Float)
    latitude = sa.Column(sa.Float)
    
    # D=For country type
    currency_code = sa.Column(sa.String(10))
    short_code = sa.Column(sa.String)
    
    emoji = sa.Column(sa.String)
    emoji_code = sa.Column(sa.String)


class Location(BaseTableModel):
    __tablename__ = 'locations'
    
    model_name = sa.Column(sa.String, nullable=True, index=True)
    model_id = sa.Column(sa.String, nullable=True, index=True)
    address = sa.Column(sa.Text)
    city = sa.Column(sa.String(50), index=True)
    state = sa.Column(sa.String(50), index=True)
    postal_code = sa.Column(sa.String(20), index=True)
    country = sa.Column(sa.String(50), index=True)
