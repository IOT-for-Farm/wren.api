from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.supplier import Supplier
from api.v1.schemas import supplier as supplier_schemas


logger = create_logger(__name__)

class SupplierService:
    pass
