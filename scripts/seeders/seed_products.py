import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.product import Product, ProductPrice
from api.v1.models.organization import Organization
from api.v1.models.user import User
from api.v1.models.vendor import Vendor
from api.db.database import get_db_with_ctx_manager


def seed_products():
    '''Seed products and their prices'''
    
    with get_db_with_ctx_manager() as db:
        # Get required dependencies
        greentrac_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="greentrac-tech"
        )
        
        admin_user = User.fetch_one_by_field(
            db=db,
            throw_error=False,
            email="admin@greentrac.com"
        )
        
        # Get a vendor for products
        solar_vendor = Vendor.fetch_one_by_field(
            db=db,
            throw_error=False,
            business_partner_id=None  # We'll find one with solar in the name
        )
        
        # Find solar vendor by checking business partner company name
        from api.v1.models.business_partner import BusinessPartner
        solar_partner = BusinessPartner.fetch_one_by_field(
            db=db,
            throw_error=False,
            partner_type="vendor"
        )
        
        if solar_partner and "solar" in solar_partner.company_name.lower():
            solar_vendor = Vendor.fetch_one_by_field(
                db=db,
                throw_error=False,
                business_partner_id=solar_partner.id
            )
        
        if not greentrac_org or not admin_user:
            print("Required dependencies not found. Please run seed_organizations.py and seed_users.py first.")
            return
        
        products = [
            {
                "name": "Monocrystalline Solar Panel 400W",
                "description": "High-efficiency monocrystalline solar panel with 400W power output. Perfect for residential and commercial installations.",
                "slug": "monocrystalline-solar-panel-400w",
                "status": "published",
                "type": "physical",
                "is_available": True,
                "attributes": {
                    "power": "400W",
                    "efficiency": "20.5%",
                    "dimensions": "2000x1000x40mm",
                    "weight": "22kg",
                    "warranty": "25 years",
                    "temperature_coefficient": "-0.35%/°C"
                },
                "additional_info": {
                    "installation_type": "roof_mounted",
                    "applications": ["residential", "commercial"],
                    "certifications": ["IEC 61215", "IEC 61730"]
                },
                "vendor_id": solar_vendor.business_partner_id if solar_vendor else None
            },
            {
                "name": "Polycrystalline Solar Panel 320W",
                "description": "Cost-effective polycrystalline solar panel with 320W power output. Ideal for budget-conscious installations.",
                "slug": "polycrystalline-solar-panel-320w",
                "status": "published",
                "type": "physical",
                "is_available": True,
                "attributes": {
                    "power": "320W",
                    "efficiency": "16.5%",
                    "dimensions": "1956x992x40mm",
                    "weight": "20kg",
                    "warranty": "25 years",
                    "temperature_coefficient": "-0.40%/°C"
                },
                "additional_info": {
                    "installation_type": "roof_mounted",
                    "applications": ["residential", "small_commercial"],
                    "certifications": ["IEC 61215", "IEC 61730"]
                },
                "vendor_id": solar_vendor.business_partner_id if solar_vendor else None
            },
            {
                "name": "Solar Inverter 5kW",
                "description": "High-efficiency string inverter for solar panel systems up to 5kW. Features MPPT tracking and monitoring capabilities.",
                "slug": "solar-inverter-5kw",
                "status": "published",
                "type": "physical",
                "is_available": True,
                "attributes": {
                    "power": "5000W",
                    "efficiency": "97.5%",
                    "input_voltage": "150-500V",
                    "output_voltage": "230V",
                    "warranty": "10 years",
                    "mppt_tracking": True
                },
                "additional_info": {
                    "installation_type": "wall_mounted",
                    "applications": ["residential", "commercial"],
                    "monitoring": "WiFi enabled",
                    "certifications": ["IEC 62109", "VDE 0126"]
                },
                "vendor_id": solar_vendor.business_partner_id if solar_vendor else None
            },
            {
                "name": "Lithium Battery 10kWh",
                "description": "High-capacity lithium-ion battery for energy storage. Perfect for off-grid and backup power applications.",
                "slug": "lithium-battery-10kwh",
                "status": "published",
                "type": "physical",
                "is_available": True,
                "attributes": {
                    "capacity": "10kWh",
                    "voltage": "48V",
                    "chemistry": "LiFePO4",
                    "cycles": "6000+",
                    "warranty": "10 years",
                    "dimensions": "600x400x200mm"
                },
                "additional_info": {
                    "installation_type": "floor_mounted",
                    "applications": ["off_grid", "backup_power", "peak_shaving"],
                    "bms": "Built-in Battery Management System",
                    "certifications": ["UL 1973", "IEC 62619"]
                },
                "vendor_id": solar_vendor.business_partner_id if solar_vendor else None
            },
            {
                "name": "Wind Turbine 1kW",
                "description": "Small wind turbine suitable for residential use. Low cut-in speed and quiet operation.",
                "slug": "wind-turbine-1kw",
                "status": "published",
                "type": "physical",
                "is_available": True,
                "attributes": {
                    "power": "1000W",
                    "cut_in_speed": "2.5 m/s",
                    "rated_speed": "12 m/s",
                    "diameter": "2.1m",
                    "height": "12m",
                    "warranty": "5 years"
                },
                "additional_info": {
                    "installation_type": "tower_mounted",
                    "applications": ["residential", "remote_locations"],
                    "noise_level": "< 45dB",
                    "certifications": ["IEC 61400", "CE"]
                },
                "vendor_id": solar_vendor.business_partner_id if solar_vendor else None
            }
        ]
        
        created_products = []
        
        for product_data in products:
            existing_product = Product.fetch_one_by_field(
                db=db,
                throw_error=False,
                slug=product_data['slug'],
                organization_id=greentrac_org.id
            )
            
            if not existing_product:
                # Add required fields
                product_data['organization_id'] = greentrac_org.id
                product_data['creator_id'] = admin_user.id
                
                new_product = Product.create(
                    db=db,
                    **product_data
                )
                created_products.append(new_product)
                print(f"Product {new_product.name} created with slug: {new_product.slug}")
                
                # Create price for the product
                price_data = {
                    "product_id": new_product.id,
                    "variant_id": None,
                    "cost_price": 0.0,  # Will be updated based on product type
                    "selling_price": 0.0,  # Will be updated based on product type
                    "currency": "NGN",
                    "start_date": None,
                    "end_date": None,
                    "min_quantity": 1,
                    "is_active": True,
                    "notes": "Default price"
                }
                
                # Set realistic prices based on product type
                if "400W" in new_product.name:
                    price_data["cost_price"] = 45000.00
                    price_data["selling_price"] = 55000.00
                elif "320W" in new_product.name:
                    price_data["cost_price"] = 35000.00
                    price_data["selling_price"] = 42000.00
                elif "5kW" in new_product.name:
                    price_data["cost_price"] = 180000.00
                    price_data["selling_price"] = 220000.00
                elif "10kWh" in new_product.name:
                    price_data["cost_price"] = 450000.00
                    price_data["selling_price"] = 550000.00
                elif "1kW" in new_product.name:
                    price_data["cost_price"] = 280000.00
                    price_data["selling_price"] = 350000.00
                
                new_price = ProductPrice.create(
                    db=db,
                    **price_data
                )
                print(f"Price created for {new_product.name}: NGN {new_price.selling_price}")
                
            else:
                print(f"Product {existing_product.name} already exists with slug: {existing_product.slug}")
        
        print(f"Total products created: {len(created_products)}")


if __name__ == "__main__":
    seed_products()
