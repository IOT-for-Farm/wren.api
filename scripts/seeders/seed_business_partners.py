import sys
import pathlib
import uuid

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.business_partner import BusinessPartner
from api.v1.models.organization import Organization
from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager


def seed_business_partners():
    '''Seed business partners (customers and vendors)'''
    
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
        
        # Get some users for reference
        admin_user = User.fetch_one_by_field(
            db=db,
            throw_error=False,
            email="admin@greentrac.com"
        )
        
        john_user = User.fetch_one_by_field(
            db=db,
            throw_error=False,
            email="john.doe@greentrac.com"
        )
        
        business_partners = [
            # Vendors
            {
            "organization_id": greentrac_org.id,
            "user_id": None,  # External vendor
            "partner_type": "vendor",
            "slug": "solar-panel-suppliers",
            "first_name": "Michael",
            "last_name": "Chen",
            "phone": "8123456701",
            "phone_country_code": "+234",
            "image_url": "https://example.com/images/michael-chen.jpg",
            "email": "michael.chen@solarpanelsuppliers.com",
            "password": None,
            "company_name": "Solar Panel Suppliers Ltd",
            "is_active": True,
            "additional_info": {
                "specialization": "Solar panel manufacturing and distribution",
                "years_in_business": 15,
                "certifications": ["ISO 9001", "IEC 61215"]
            },
                "notes": "Reliable supplier of high-quality solar panels"
            },
            {
            "organization_id": greentrac_org.id,
            "user_id": None,
            "partner_type": "vendor",
            "slug": "wind-energy-solutions",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "phone": "8123456702",
            "phone_country_code": "+234",
            "image_url": "https://example.com/images/sarah-johnson.jpg",
            "email": "sarah.johnson@windenergy.com",
            "password": None,
            "company_name": "Wind Energy Solutions Inc",
            "is_active": True,
            "additional_info": {
                "specialization": "Wind turbine installation and maintenance",
                "years_in_business": 8,
                "certifications": ["ISO 14001", "OHSAS 18001"]
            },
                "notes": "Expert in wind energy solutions for commercial and residential use"
            },
            {
            "organization_id": greentrac_org.id,
            "user_id": None,
            "partner_type": "vendor",
            "slug": "eco-materials-co",
            "first_name": "David",
            "last_name": "Okafor",
            "phone": "8123456703",
            "phone_country_code": "+234",
            "image_url": "https://example.com/images/david-okafor.jpg",
            "email": "david.okafor@ecomaterials.com",
            "password": None,
            "company_name": "Eco Materials Company",
            "is_active": True,
            "additional_info": {
                "specialization": "Sustainable building materials",
                "years_in_business": 12,
                "certifications": ["LEED", "Green Building Council"]
            },
                "notes": "Leading supplier of eco-friendly building materials"
            },
            
            # Customers
            {
            "organization_id": greentrac_org.id,
            "user_id": john_user.id if john_user else None,
            "partner_type": "customer",
            "slug": "green-office-spaces",
            "first_name": "Emma",
            "last_name": "Williams",
            "phone": "8123456704",
            "phone_country_code": "+234",
            "image_url": "https://example.com/images/emma-williams.jpg",
            "email": "emma.williams@greenofficespaces.com",
            "password": None,
            "company_name": "Green Office Spaces Ltd",
            "is_active": True,
            "additional_info": {
                "industry": "Real Estate",
                "company_size": "50-100 employees",
                "sustainability_goals": ["Net zero emissions by 2030", "LEED certification"]
            },
                "notes": "Looking to implement sustainable practices in office buildings"
            },
            {
            "organization_id": greentrac_org.id,
            "user_id": None,
            "partner_type": "customer",
            "slug": "eco-manufacturing-ltd",
            "first_name": "James",
            "last_name": "Brown",
            "phone": "8123456705",
            "phone_country_code": "+234",
            "image_url": "https://example.com/images/james-brown.jpg",
            "email": "james.brown@ecomanufacturing.com",
            "password": None,
            "company_name": "Eco Manufacturing Ltd",
            "is_active": True,
            "additional_info": {
                "industry": "Manufacturing",
                "company_size": "200-500 employees",
                "sustainability_goals": ["Reduce waste by 50%", "Switch to renewable energy"]
            },
                "notes": "Manufacturing company seeking to reduce environmental impact"
            },
            {
            "organization_id": ecofriendly_org.id,
            "user_id": None,
            "partner_type": "customer",
            "slug": "sustainable-retail-chain",
            "first_name": "Lisa",
            "last_name": "Davis",
            "phone": "8123456706",
            "phone_country_code": "+234",
            "image_url": "https://example.com/images/lisa-davis.jpg",
            "email": "lisa.davis@sustainableretail.com",
            "password": None,
            "company_name": "Sustainable Retail Chain",
            "is_active": True,
            "additional_info": {
                "industry": "Retail",
                "company_size": "100-200 employees",
                "sustainability_goals": ["Plastic-free packaging", "Carbon neutral operations"]
            },
                "notes": "Retail chain committed to sustainable practices"
            }
        ]
    
        for partner_data in business_partners:
            existing_partner = BusinessPartner.fetch_one_by_field(
                db=db, 
                throw_error=False,
                slug=partner_data['slug'],
                organization_id=partner_data['organization_id']
            )
            
            if not existing_partner:
                new_partner = BusinessPartner.create(
                    db=db,
                    **partner_data
                )
                print(f"BusinessPartner {new_partner.first_name} {new_partner.last_name} ({new_partner.partner_type}) created")
            else:
                print(f"BusinessPartner {existing_partner.first_name} {existing_partner.last_name} ({existing_partner.partner_type}) already exists")


if __name__ == "__main__":
    seed_business_partners()
