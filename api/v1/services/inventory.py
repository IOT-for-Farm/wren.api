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
        operation: str = 'add'  # or remove
    ):
        '''This function checks if an inventory has the required amount to remove'''
        
        if operation not in ['add', 'remove']:
            raise ValueError(f'Expecting add or remove and got `{operation}')
        
        if variant_id:
            inventory = Inventory.fetch_one_by_field(
                db=db,
                product_id=product_id,
                variant_id=variant_id
            )
        else:
            inventory = Inventory.fetch_one_by_field(db=db, product_id=product_id)
            
        if quantity_to_update > 0 and (inventory.quantity < quantity_to_update) and operation == 'remove':
            raise HTTPException(400, f"Only {inventory.quantity} items are available for {inventory.product.name}, you requested for {quantity_to_update}")

        logger.info(f'Inventory quantity to update: {quantity_to_update}')
        
        if operation == 'add':
            inventory.quantity += quantity_to_update
        else:
            inventory.quantity -= quantity_to_update
        
        db.commit()
