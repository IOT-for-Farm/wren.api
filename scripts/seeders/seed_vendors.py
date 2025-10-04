import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.vendor import Vendor
from api.v1.models.business_partner import BusinessPartner
from api.db.database import get_db_with_ctx_manager


def seed_vendors():
    '''Seed vendors (extending business partners)'''
    
    with get_db_with_ctx_manager() as db:
        # Get business partners that are vendors
        vendor_partners = BusinessPartner.fetch_by_field(
            db=db,
            paginate=False,
            partner_type="vendor"
        )[1]  # Get the results, not the query
        
        if not vendor_partners:
            print("No vendor business partners found. Please run seed_business_partners.py first.")
            return
        
        vendors = []
        
        for partner in vendor_partners:
            # Check if vendor already exists for this business partner
            existing_vendor = Vendor.fetch_one_by_field(
                db=db,
                throw_error=False,
                business_partner_id=partner.id
            )
            
            if not existing_vendor:
                # Create vendor with additional vendor-specific fields
                vendor_data = {
                    "business_partner_id": partner.id,
                    "organization_id": partner.organization_id,
                    "vendor_type": "supplier",  # Default vendor type
                    "contact_person_name": f"{partner.first_name} {partner.last_name}",
                    "contact_person_email": partner.email,
                    "contact_person_phone": partner.phone,
                    "contact_person_phone_country_code": partner.phone_country_code,
                    "payment_terms": "net_30",  # Default payment terms
                    "commission_percentage": 5.0  # Default commission
                }
                
                # Customize based on company name
                if partner.company_name and "solar" in partner.company_name.lower():
                    vendor_data["vendor_type"] = "manufacturer"
                    vendor_data["payment_terms"] = "prepaid"
                    vendor_data["commission_percentage"] = 3.0
                elif partner.company_name and "wind" in partner.company_name.lower():
                    vendor_data["vendor_type"] = "service_provider"
                    vendor_data["payment_terms"] = "net_45"
                    vendor_data["commission_percentage"] = 7.0
                elif partner.company_name and "eco" in partner.company_name.lower():
                    vendor_data["vendor_type"] = "supplier"
                    vendor_data["payment_terms"] = "net_30"
                    vendor_data["commission_percentage"] = 4.0
                
                new_vendor = Vendor.create(
                    db=db,
                    **vendor_data
                )
                vendors.append(new_vendor)
                print(f"Vendor created for {partner.first_name} {partner.last_name} ({partner.company_name})")
            else:
                print(f"Vendor already exists for {partner.first_name} {partner.last_name}")
        
        print(f"Total vendors processed: {len(vendors)}")


if __name__ == "__main__":
    seed_vendors()
