# Database Seeders

This directory contains seed scripts for populating the database with initial data. The seeders are designed to run in a specific dependency order to avoid foreign key constraint errors.

## Usage

### Run All Seeders (Recommended)

```bash
# From the project root
./scripts/run_seeders.sh

# Or directly
python3 scripts/seeders/run_all_seeders.py
```

### Run Individual Seeders

You can run individual seeders, but make sure to run them in dependency order:

```bash
# Level 1 (No dependencies)
python3 scripts/seeders/seed_users.py
python3 scripts/seeders/seed_base_locations.py
python3 scripts/seeders/seed_organizations.py

# Level 2 (Depend on Level 1)
python3 scripts/seeders/seed_business_partners.py
python3 scripts/seeders/seed_categories.py

# Level 3 (Depend on Level 2)
python3 scripts/seeders/seed_customers.py
python3 scripts/seeders/seed_vendors.py
python3 scripts/seeders/seed_accounts.py
python3 scripts/seeders/seed_products.py

# Level 4 (Depend on Level 3)
python3 scripts/seeders/seed_inventory.py
python3 scripts/seeders/seed_orders.py
python3 scripts/seeders/seed_events.py

# Level 5 (Depend on Level 4)
python3 scripts/seeders/seed_invoices.py
python3 scripts/seeders/seed_payments.py
python3 scripts/seeders/seed_receipts.py
python3 scripts/seeders/seed_sales.py

# Level 6 (Depend on Level 5)
python3 scripts/seeders/seed_projects.py
python3 scripts/seeders/seed_tasks.py

# Level 7 (Depend on Level 6)
python3 scripts/seeders/seed_departments.py
python3 scripts/seeders/seed_department_budgets.py
```

## Dependency Order

The seeders are organized in dependency levels:

### Level 1: Base Tables (No Dependencies)
- `seed_users.py` - User accounts
- `seed_base_locations.py` - Geographic locations (continents, countries, states, cities)
- `seed_organizations.py` - Organizations

### Level 2: Dependent on Level 1
- `seed_business_partners.py` - Business partners (customers/vendors)
- `seed_categories.py` - Categories for products, vendors, content, customers
- Existing seeders: `seed_org_role_permissions.py`, `seed_template_layouts.py`, etc.

### Level 3: Dependent on Level 2
- `seed_customers.py` - Customer extensions
- `seed_vendors.py` - Vendor extensions
- `seed_accounts.py` - Customer/vendor accounts
- `seed_products.py` - Products and product prices

### Level 4: Dependent on Level 3
- `seed_inventory.py` - Product inventory
- `seed_orders.py` - Customer orders and order items
- `seed_events.py` - Events and event attendees

### Level 5: Dependent on Level 4
- `seed_invoices.py` - Customer and vendor invoices
- `seed_payments.py` - Payment records for invoices
- `seed_receipts.py` - Receipts for paid invoices
- `seed_sales.py` - Sales transactions and profit tracking

### Level 6: Dependent on Level 5
- `seed_projects.py` - Projects, milestones, and project members
- `seed_tasks.py` - Project tasks and task assignees

### Level 7: Dependent on Level 6
- `seed_departments.py` - Departments, roles, and department members
- `seed_department_budgets.py` - Department budgets and budget adjustments

## Data Created

### Users
- Admin user (admin@greentrac.com)
- Regular users (john.doe, jane.smith, etc.)

### Organizations
- GreenTrac Technologies
- EcoFriendly Solutions Ltd
- GreenTech Innovations
- Sustainable Business Hub
- Green Finance Corp

### Business Partners
- Solar panel suppliers
- Wind energy companies
- Eco-material suppliers
- Various customers

### Products
- Solar panels (monocrystalline and polycrystalline)
- Solar inverters
- Lithium batteries
- Wind turbines

### Categories
- Product categories (Solar Energy, Wind Energy, etc.)
- Vendor categories (Equipment Suppliers, Installation Services)
- Content categories (News, Technology, Sustainability)
- Customer categories (Commercial, Residential, Government)

### Orders
- Sample orders for each customer
- Order items with realistic quantities

### Events
- Solar Energy Workshop
- Weekly Green Tech Meetup
- Environmental Impact Assessment Training
- Product Launch Events

### Invoices & Payments
- Customer invoices for orders
- Vendor invoices for supplies
- Payment records with various methods
- Receipts for completed transactions

### Sales
- Sales records for products
- Profit calculations and vendor commissions
- Customer purchase history

### Projects
- Solar Installation Project
- Green Energy Awareness Campaign
- Wind Farm Feasibility Study
- Mobile App Development
- Project milestones and tasks

### Departments
- Engineering, Sales & Marketing, Customer Success
- Solar Installation, Project Management
- Environmental Consulting, Research & Development
- Department budgets with quarterly breakdowns
- Budget adjustments and approvals

## Notes

- All seeders are idempotent - they can be run multiple times safely
- Existing records are skipped to avoid duplicates
- Realistic sample data is created for testing and development
- Foreign key relationships are properly maintained
- The master seeder script (`run_all_seeders.py`) handles the dependency order automatically

## Troubleshooting

If you encounter foreign key constraint errors:
1. Make sure you're running seeders in the correct order
2. Check that dependent records exist before creating referencing records
3. Use the master seeder script which handles dependencies automatically

If you need to reset the database:
1. Drop and recreate the database
2. Run migrations
3. Run the seeders
