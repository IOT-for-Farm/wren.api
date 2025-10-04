import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.inventory import Inventory
from api.v1.models.product import Product
from api.db.database import get_db_with_ctx_manager


def seed_inventory():
    '''Seed inventory for products'''
    
    with get_db_with_ctx_manager() as db:
        # Get all products
        products = Product.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if not products:
            print("No products found. Please run seed_products.py first.")
            return
        
        created_inventory = []
    
    for product in products:
        # Check if inventory already exists for this product
        existing_inventory = Inventory.fetch_one_by_field(
            db=db,
            throw_error=False,
            product_id=product.id,
            is_active=True
        )
        
        if not existing_inventory:
            # Create inventory with appropriate stock levels
            inventory_data = {
                "product_id": product.id,
                "variant_id": None,
                "quantity": 0,  # Will be set based on product type
                "reorder_threshold": 10,  # Default threshold
                "reorder_amount": 50,  # Default reorder amount
                "is_active": True
            }
            
            # Set realistic stock levels based on product type
            if "400W" in product.name:
                inventory_data["quantity"] = 25
                inventory_data["reorder_threshold"] = 5
                inventory_data["reorder_amount"] = 20
            elif "320W" in product.name:
                inventory_data["quantity"] = 30
                inventory_data["reorder_threshold"] = 8
                inventory_data["reorder_amount"] = 25
            elif "5kW" in product.name:
                inventory_data["quantity"] = 8
                inventory_data["reorder_threshold"] = 2
                inventory_data["reorder_amount"] = 10
            elif "10kWh" in product.name:
                inventory_data["quantity"] = 5
                inventory_data["reorder_threshold"] = 1
                inventory_data["reorder_amount"] = 5
            elif "1kW" in product.name:
                inventory_data["quantity"] = 3
                inventory_data["reorder_threshold"] = 1
                inventory_data["reorder_amount"] = 5
            else:
                # Default values for other products
                inventory_data["quantity"] = 15
                inventory_data["reorder_threshold"] = 5
                inventory_data["reorder_amount"] = 20
            
            new_inventory = Inventory.create(
                db=db,
                **inventory_data
            )
            created_inventory.append(new_inventory)
            print(f"Inventory created for {product.name}: {new_inventory.quantity} units")
        else:
            print(f"Inventory already exists for {product.name}: {existing_inventory.quantity} units")
    
    print(f"Total inventory records created: {len(created_inventory)}")


if __name__ == "__main__":
    seed_inventory()
