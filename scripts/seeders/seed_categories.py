import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.category import Category
from api.v1.models.organization import Organization
from api.db.database import get_db_with_ctx_manager


def seed_categories():
    '''Seed categories for different model types'''
    
    with get_db_with_ctx_manager() as db:
        # Get organizations
        greentrac_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="greentrac-tech"
        )
    
        ecofriendly_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="ecofriendly-solutions"
        )
        
        if not greentrac_org or not ecofriendly_org:
            print("Required organizations not found. Please run seed_organizations.py first.")
            return
        
        categories = [
            # Product Categories
            {
                "name": "Solar Energy",
                "description": "Solar panels, inverters, and related equipment",
                "slug": "solar-energy",
                "model_type": "products",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Wind Energy",
                "description": "Wind turbines and wind energy equipment",
                "slug": "wind-energy",
                "model_type": "products",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Energy Storage",
                "description": "Batteries and energy storage solutions",
                "slug": "energy-storage",
                "model_type": "products",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Solar Panels",
                "description": "Various types of solar panels",
                "slug": "solar-panels",
                "model_type": "products",
                "parent_id": None,  # Will be set after parent is created
                "organization_id": greentrac_org.id
            },
            {
                "name": "Monocrystalline Panels",
                "description": "High-efficiency monocrystalline solar panels",
                "slug": "monocrystalline-panels",
                "model_type": "products",
                "parent_id": None,  # Will be set after parent is created
                "organization_id": greentrac_org.id
            },
            {
                "name": "Polycrystalline Panels",
                "description": "Cost-effective polycrystalline solar panels",
                "slug": "polycrystalline-panels",
                "model_type": "products",
                "parent_id": None,  # Will be set after parent is created
                "organization_id": greentrac_org.id
            },
            
            # Vendor Categories
            {
                "name": "Equipment Suppliers",
                "description": "Suppliers of renewable energy equipment",
                "slug": "equipment-suppliers",
                "model_type": "vendors",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Installation Services",
                "description": "Companies providing installation services",
                "slug": "installation-services",
                "model_type": "vendors",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Consulting Services",
                "description": "Environmental and sustainability consulting",
                "slug": "consulting-services",
                "model_type": "vendors",
                "parent_id": None,
                "organization_id": ecofriendly_org.id
            },
            
            # Content Categories
            {
                "name": "News",
                "description": "Latest news and updates",
                "slug": "news",
                "model_type": "content",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Technology",
                "description": "Technology-related content",
                "slug": "technology",
                "model_type": "content",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Sustainability",
                "description": "Sustainability and environmental content",
                "slug": "sustainability",
                "model_type": "content",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            
            # Customer Categories
            {
                "name": "Commercial",
                "description": "Commercial and business customers",
                "slug": "commercial",
                "model_type": "customers",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Residential",
                "description": "Residential customers",
                "slug": "residential",
                "model_type": "customers",
                "parent_id": None,
                "organization_id": greentrac_org.id
            },
            {
                "name": "Government",
                "description": "Government and public sector customers",
                "slug": "government",
                "model_type": "customers",
                "parent_id": None,
                "organization_id": greentrac_org.id
            }
        ]
        
        # Create a mapping to store created categories for parent references
        created_categories = {}
        
        for category_data in categories:
            # Skip parent_id for now, we'll set it after creating parent categories
            category_data_copy = category_data.copy()
            parent_id = category_data_copy.pop('parent_id', None)
            
            existing_category = Category.fetch_one_by_field(
                db=db, 
                throw_error=False,
                name=category_data['name'],
                model_type=category_data['model_type'],
                organization_id=category_data['organization_id']
            )
            
            if not existing_category:
                new_category = Category.create(
                    db=db,
                    **category_data_copy
                )
                created_categories[f"{category_data['name']}_{category_data['model_type']}"] = new_category.id
                print(f"Category {new_category.name} ({new_category.model_type}) created")
            else:
                created_categories[f"{category_data['name']}_{category_data['model_type']}"] = existing_category.id
                print(f"Category {existing_category.name} ({existing_category.model_type}) already exists")
        
        # Now update parent_id references
        parent_child_mappings = [
            ("Solar Energy", "Solar Panels"),
            ("Solar Panels", "Monocrystalline Panels"),
            ("Solar Panels", "Polycrystalline Panels"),
        ]
        
        for parent_name, child_name in parent_child_mappings:
            parent_key = f"{parent_name}_products"
            child_key = f"{child_name}_products"
            
            if parent_key in created_categories and child_key in created_categories:
                # Find the child category and update its parent_id
                child_category = Category.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    name=child_name,
                    model_type="products",
                    organization_id=greentrac_org.id
                )
                if child_category and not child_category.parent_id:
                    child_category.parent_id = created_categories[parent_key]
                    db.commit()
                    print(f"Updated parent_id for {child_category.name} to {parent_name}")


if __name__ == "__main__":
    seed_categories()
