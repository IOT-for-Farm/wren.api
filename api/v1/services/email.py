from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.email import Email
from api.v1.schemas import email as email_schemas


logger = create_logger(__name__)

class EmailService:
    pass
