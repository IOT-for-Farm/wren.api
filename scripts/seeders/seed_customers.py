import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.customer import Customer
from api.v1.models.business_partner import BusinessPartner
from api.db.database import get_db_with_ctx_manager


def seed_customers():
    '''Seed customers (extending business partners)'''
    
    with get_db_with_ctx_manager() as db:
        # Get business partners that are customers
        customer_partners = BusinessPartner.fetch_by_field(
            db=db,
            paginate=False,
            partner_type="customer"
        )[1]  # Get the results, not the query
        
        if not customer_partners:
            print("No customer business partners found. Please run seed_business_partners.py first.")
            return
        
        customers = []
        
        for partner in customer_partners:
            # Check if customer already exists for this business partner
            existing_customer = Customer.fetch_one_by_field(
                db=db,
                throw_error=False,
                business_partner_id=partner.id
            )
            
            if not existing_customer:
                # Create customer with additional customer-specific fields
                customer_data = {
                    "business_partner_id": partner.id,
                    "organization_id": partner.organization_id,
                    "language": "en",
                    "gender": "prefer_not_to_say",
                    "age": None,
                    "customer_type": "business" if partner.company_name else "individual",
                    "industry": partner.additional_info.get("industry") if partner.additional_info else None,
                    "preferred_payment_method": "bank_transfer"
                }
                
                new_customer = Customer.create(
                    db=db,
                    **customer_data
                )
                customers.append(new_customer)
                print(f"Customer created for {partner.first_name} {partner.last_name}")
            else:
                print(f"Customer already exists for {partner.first_name} {partner.last_name}")
        
        print(f"Total customers processed: {len(customers)}")


if __name__ == "__main__":
    seed_customers()
