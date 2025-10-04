#!/usr/bin/env python3
"""
Master script to run all database seeders in the correct dependency order.
This ensures that tables are seeded in the proper sequence to avoid foreign key constraint errors.
"""

import sys
import pathlib
import importlib.util

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

def run_seeder(seeder_name):
    """Run a specific seeder script"""
    print(f"\n{'='*60}")
    print(f"Running {seeder_name}")
    print(f"{'='*60}")
    
    try:
        # Import and run the seeder
        seeder_path = pathlib.Path(__file__).parent / f"{seeder_name}.py"
        
        if not seeder_path.exists():
            print(f"Warning: {seeder_name}.py not found, skipping...")
            return True
        
        spec = importlib.util.spec_from_file_location(seeder_name, seeder_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Call the main function if it exists
        if hasattr(module, 'seed_' + seeder_name.replace('seed_', '')):
            seed_func = getattr(module, 'seed_' + seeder_name.replace('seed_', ''))
            seed_func()
        elif hasattr(module, seeder_name.replace('seed_', '')):
            seed_func = getattr(module, seeder_name.replace('seed_', ''))
            seed_func()
        else:
            print(f"Warning: No seed function found in {seeder_name}.py")
        
        print(f"✅ {seeder_name} completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error running {seeder_name}: {str(e)}")
        return False

def main():
    """Main function to run all seeders in dependency order"""
    
    print("🌱 Starting Database Seeding Process")
    print("="*60)
    
    # Define seeders in dependency order (from least to most dependent)
    seeders = [
        # Level 1: No dependencies
        "seed_users",
        "seed_base_locations", 
        "seed_organizations",
        
        # Level 2: Depend on Level 1
        # "seed_org_role_permissions",  # Existing seeder
        # "seed_template_layouts",      # Existing seeder
        # "seed_email_templates",       # Existing seeder
        # "seed_content_templates",     # Existing seeder
        # "seed_form_templates",        # Existing seeder
        "seed_business_partners",
        "seed_categories",
        
        # Level 3: Depend on Level 2
        "seed_customers",
        "seed_vendors", 
        "seed_accounts",
        "seed_products",
        
        # Level 4: Depend on Level 3
        "seed_inventory",
        "seed_orders",
        "seed_events",
        
        # Level 5: Depend on Level 4 (invoices, payments, etc.)
        "seed_invoices",
        "seed_payments", 
        "seed_receipts",
        "seed_sales",
        
        # Level 6: Depend on Level 5
        "seed_projects",
        "seed_tasks",
        
        # Level 7: Depend on Level 6
        "seed_departments",
        "seed_department_budgets",
    ]
    
    successful = 0
    failed = 0
    
    for seeder in seeders:
        if run_seeder(seeder):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print("🌱 Database Seeding Process Complete")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {successful + failed}")
    
    if failed > 0:
        print("\n⚠️  Some seeders failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n🎉 All seeders completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
