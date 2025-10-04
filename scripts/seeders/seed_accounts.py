import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.account import Account
from api.v1.models.organization import Organization
from api.v1.models.customer import Customer
from api.v1.models.vendor import Vendor
from api.db.database import get_db_with_ctx_manager


def seed_accounts():
    '''Seed accounts for customers and vendors'''
    
    with get_db_with_ctx_manager() as db:
        # Get organizations
        greentrac_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="greentrac-tech"
        )
        
        if not greentrac_org:
            print("Required organization not found. Please run seed_organizations.py first.")
            return
        
        # Get customers
        customers = Customer.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        # Get vendors
        vendors = Vendor.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        accounts = []
        
        # Create accounts for customers
        for customer in customers:
            existing_account = Account.fetch_one_by_field(
                db=db,
                throw_error=False,
                owner_type="customer",
                owner_id=customer.business_partner_id,
                organization_id=greentrac_org.id
            )
            
            if not existing_account:
                account_data = {
                    "organization_id": greentrac_org.id,
                    "owner_type": "customer",
                    "owner_id": customer.business_partner_id,
                    "balance": 0.00,
                    "amount_owing": 0.00,
                    "amount_owed": 0.00,
                    "currency_code": "NGN",
                    "credit_limit": 1000000.00,  # 1M NGN credit limit
                    "credit_allowed": True,
                    "is_active": True
                }
                
                new_account = Account.create(
                    db=db,
                    **account_data
                )
                accounts.append(new_account)
                print(f"Account created for customer {customer.business_partner_id}")
            else:
                print(f"Account already exists for customer {customer.business_partner_id}")
        
        # Create accounts for vendors
        for vendor in vendors:
            existing_account = Account.fetch_one_by_field(
                db=db,
                throw_error=False,
                owner_type="vendor",
                owner_id=vendor.business_partner_id,
                organization_id=greentrac_org.id
            )
            
            if not existing_account:
                account_data = {
                    "organization_id": greentrac_org.id,
                    "owner_type": "vendor",
                    "owner_id": vendor.business_partner_id,
                    "balance": 0.00,
                    "amount_owing": 0.00,
                    "amount_owed": 0.00,
                    "currency_code": "NGN",
                    "credit_limit": 0.00,  # Vendors typically don't get credit
                    "credit_allowed": False,
                    "is_active": True
                }
                
                new_account = Account.create(
                    db=db,
                    **account_data
                )
                accounts.append(new_account)
                print(f"Account created for vendor {vendor.business_partner_id}")
            else:
                print(f"Account already exists for vendor {vendor.business_partner_id}")
        
        print(f"Total accounts created: {len(accounts)}")


if __name__ == "__main__":
    seed_accounts()
