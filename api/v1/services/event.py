from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.event import Event
from api.v1.schemas import event as event_schemas


logger = create_logger(__name__)

class EventService:
    pass
