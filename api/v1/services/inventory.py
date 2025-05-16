from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.inventory import Inventory
from api.v1.schemas import inventory as inventory_schemas


logger = create_logger(__name__)

class InventoryService:
    
    @classmethod
    def check_and_update_inventory(
        cls,
        db: Session,
        quantity_to_update: int,
        product_id: str,
        variant_id: Optional[str]=None,
    ):
        '''This function checks if an inventory has the required amount to remove'''
        
        if variant_id:
            inventory = Inventory.fetch_one_by_field(
                db=db,
                product_id=product_id,
                variant_id=variant_id
            )
        else:
            inventory = Inventory.fetch_one_by_field(db=db, product_id=product_id)
            
        if quantity_to_update > 0 and (inventory.quantity < quantity_to_update):
            raise HTTPException(400, "Low on inventory. The amount requested for is too high")

        logger.info(f'Inventory quantity to update: {quantity_to_update}')
        inventory.quantity -= quantity_to_update
        
        db.commit()
