from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.inventory import Inventory
from api.v1.schemas import inventory as inventory_schemas


logger = create_logger(__name__)

class InventoryService:
    pass
