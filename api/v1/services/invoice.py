from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.invoice import Invoice
from api.v1.schemas import invoice as invoice_schemas


logger = create_logger(__name__)

class InvoiceService:
    pass
