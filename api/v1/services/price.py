from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.product import ProductPrice
from api.v1.schemas import price as price_schemas


logger = create_logger(__name__)

class PriceService:
    
    @classmethod
    def deactivate_active_prices(cls, db: Session, product_id: str):
        '''Function to deactive active product prices. 
        Useful before creating or updating a product price to active status of true'''
        
        query, prices_to_deactivate, count = ProductPrice.fetch_by_field(
            db=db,
            paginate=False,
            is_active=True,
            product_id=product_id
        )
        
        for p in prices_to_deactivate:
            p.is_active = False
        
        db.commit()
