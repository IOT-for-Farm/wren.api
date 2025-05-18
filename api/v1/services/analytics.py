from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.analytics import Analytics
from api.v1.schemas import analytics as analytics_schemas


logger = create_logger(__name__)

class AnalyticsService:
    pass
