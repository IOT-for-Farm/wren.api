from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.webhook import Webhook
from api.v1.schemas import webhook as webhook_schemas


logger = create_logger(__name__)

class WebhookService:
    pass
