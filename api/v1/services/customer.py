from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.customer import Customer
from api.v1.schemas import customer as customer_schemas


logger = create_logger(__name__)

class CustomerService:
    pass
