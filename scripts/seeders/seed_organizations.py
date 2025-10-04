import sys
import pathlib
import uuid

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.utils.helpers import generate_logo_url
from api.v1.models.organization import Organization, OrganizationMember, OrganizationRole
from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager
from api.core.dependencies.permissions import ROLE_PERMISSIONS


def seed_organizations():
    '''Seed organizations'''
    
    with get_db_with_ctx_manager() as db:
        # Get admin user to be the creator
        admin_user = User.fetch_one_by_field(
            db=db,
            throw_error=False,
            email="admin@greentrac.com"
        )
        
        if not admin_user:
            print("Admin user not found. Please run seed_users.py first.")
            return
        
        # Get all users for role assignment
        all_users = User.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if len(all_users) < 4:
            print("Not enough users found. Please run seed_users.py first.")
            return
        
        organizations = [
            {
                "name": "GreenTrac Technologies",
                "slug": "greentrac-tech",
                "description": "Leading provider of sustainable technology solutions for businesses",
                "logo_url": generate_logo_url("GreenTrac Technologies"),
                "website": "https://greentrac.com",
                "social_media_links": {
                    "twitter": "https://twitter.com/greentrac",
                    "linkedin": "https://linkedin.com/company/greentrac",
                    "facebook": "https://facebook.com/greentrac"
                },
                "policy": "Our privacy policy ensures your data is protected and used responsibly.",
                "terms_and_conditions": "By using our services, you agree to our terms and conditions.",
                "mission": "To accelerate the transition to sustainable business practices through innovative technology solutions.",
                "vision": "A world where every business operates sustainably and efficiently.",
                "initials": "GT",
                "business_type": "technology",
                "tagline": "Sustainable Technology Solutions",
                "timezone": "Africa/Lagos",
                "currency": "NGN",
                "created_by": admin_user.id
            },
            {
                "name": "EcoFriendly Solutions Ltd",
                "slug": "ecofriendly-solutions",
                "description": "Environmental consulting and sustainable development solutions",
                "logo_url": generate_logo_url("EcoFriendly Solutions Ltd"),
                "website": "https://ecofriendly-solutions.com",
                "social_media_links": {
                    "twitter": "https://twitter.com/ecofriendly",
                    "linkedin": "https://linkedin.com/company/ecofriendly-solutions"
                },
                "policy": "We are committed to environmental protection and sustainable practices.",
                "terms_and_conditions": "Terms and conditions for environmental consulting services.",
                "mission": "To help businesses reduce their environmental impact through innovative solutions.",
                "vision": "A sustainable future for all businesses and communities.",
                "initials": "EF",
                "business_type": "consulting",
                "tagline": "Green Solutions for a Better Tomorrow",
                "timezone": "Africa/Lagos",
                "currency": "NGN",
                "created_by": admin_user.id
            },
            {
                "name": "GreenTech Innovations",
                "slug": "greentech-innovations",
                "description": "Innovative green technology solutions for modern businesses",
                "logo_url": generate_logo_url("GreenTech Innovations"),
                "website": "https://greentech-innovations.com",
                "social_media_links": {
                    "twitter": "https://twitter.com/greentech_innov",
                    "linkedin": "https://linkedin.com/company/greentech-innovations",
                    "instagram": "https://instagram.com/greentech_innovations"
                },
                "policy": "Your data privacy and security are our top priorities.",
                "terms_and_conditions": "Standard terms and conditions for our technology services.",
                "mission": "To revolutionize how businesses approach sustainability through cutting-edge technology.",
                "vision": "Empowering businesses to achieve net-zero emissions through technology.",
                "initials": "GI",
                "business_type": "technology",
                "tagline": "Innovation Meets Sustainability",
                "timezone": "America/New_York",
                "currency": "USD",
                "created_by": admin_user.id
            },
            {
                "name": "Sustainable Business Hub",
                "slug": "sustainable-business-hub",
                "description": "A platform connecting sustainable businesses and providing resources",
                "logo_url": generate_logo_url("Sustainable Business Hub"),
                "website": "https://sustainable-business-hub.com",
                "social_media_links": {
                    "twitter": "https://twitter.com/sustainable_hub",
                    "linkedin": "https://linkedin.com/company/sustainable-business-hub",
                    "youtube": "https://youtube.com/sustainablebusinesshub"
                },
                "policy": "We respect your privacy and are committed to protecting your personal information.",
                "terms_and_conditions": "Platform terms and conditions for sustainable business networking.",
                "mission": "To create a global network of sustainable businesses and provide them with the tools they need to succeed.",
                "vision": "A thriving ecosystem of sustainable businesses worldwide.",
                "initials": "SBH",
                "business_type": "platform",
                "tagline": "Connecting Sustainable Businesses",
                "timezone": "Europe/London",
                "currency": "GBP",
                "created_by": admin_user.id
            },
            {
                "name": "Green Finance Corp",
                "slug": "green-finance-corp",
                "description": "Financial services specializing in sustainable and green investments",
                "logo_url": generate_logo_url("Green Finance Corp"),
                "website": "https://green-finance-corp.com",
                "social_media_links": {
                    "twitter": "https://twitter.com/greenfinance",
                    "linkedin": "https://linkedin.com/company/green-finance-corp"
                },
                "policy": "Financial data protection and regulatory compliance are our core principles.",
                "terms_and_conditions": "Financial services terms and conditions.",
                "mission": "To provide financial solutions that support sustainable business growth and environmental responsibility.",
                "vision": "A financial system that prioritizes sustainability and long-term value creation.",
                "initials": "GFC",
                "business_type": "finance",
                "tagline": "Financing a Sustainable Future",
                "timezone": "America/New_York",
                "currency": "USD",
                "created_by": admin_user.id
            }
        ]
        
        for org_data in organizations:
            existing_org = Organization.fetch_one_by_field(
                db=db, 
                throw_error=False,
                slug=org_data['slug']
            )
            
            if not existing_org:
                new_org = Organization.create(
                    db=db,
                    **org_data
                )
                print(f"Organization {new_org.name} created with slug: {new_org.slug}")
                
                # Create organization roles
                org_roles = {
                    "Owner": ROLE_PERMISSIONS["Owner"],
                    "Admin": ROLE_PERMISSIONS["Admin"],
                    "Agent": ROLE_PERMISSIONS["Agent"],
                    "Content Manager": ROLE_PERMISSIONS["Content Manager"],
                    "Campaign Manager": ROLE_PERMISSIONS["Campaign Manager"]
                }
                
                created_roles = {}
                for role_name, permissions in org_roles.items():
                    existing_role = OrganizationRole.fetch_one_by_field(
                        db=db,
                        throw_error=False,
                        organization_id='-1',
                        role_name=role_name
                    )
                    
                    if not existing_role:
                        created_role = OrganizationRole.create(
                            db=db,
                            organization_id='-1',
                            role_name=role_name,
                            permissions=permissions
                        )
                        created_roles[role_name] = created_role
                        print(f"  - {role_name} role created for {new_org.name}")
                    else:
                        created_roles[role_name] = existing_role
                
                # Assign users to different roles
                user_role_assignments = [
                    {
                        "user": admin_user,
                        "role": "Owner",
                        "title": "Owner & Founder"
                    },
                    {
                        "user": all_users[1] if len(all_users) > 1 else admin_user,  # John Doe
                        "role": "Admin",
                        "title": "Administrator"
                    },
                    {
                        "user": all_users[2] if len(all_users) > 2 else admin_user,  # Jane Smith
                        "role": "Agent",
                        "title": "Business Agent"
                    },
                    {
                        "user": all_users[3] if len(all_users) > 3 else admin_user,  # Mike Wilson
                        "role": "Content Manager",
                        "title": "Content Manager"
                    },
                    {
                        "user": all_users[4] if len(all_users) > 4 else admin_user,  # Sarah Johnson
                        "role": "Campaign Manager",
                        "title": "Campaign Manager"
                    }
                ]
                
                for assignment in user_role_assignments:
                    user = assignment["user"]
                    role_name = assignment["role"]
                    title = assignment["title"]
                    
                    existing_member = OrganizationMember.fetch_one_by_field(
                        db=db,
                        throw_error=False,
                        organization_id=new_org.id,
                        user_id=user.id
                    )
                    
                    if not existing_member:
                        OrganizationMember.create(
                            db=db,
                            organization_id=new_org.id,
                            user_id=user.id,
                            role_id=created_roles[role_name].id,
                            title=title,
                            is_primary_contact=(role_name == "Owner"),
                            is_active=True
                        )
                        print(f"  - {user.first_name} {user.last_name} added as {role_name} ({title})")
                
            else:
                print(f"Organization {existing_org.name} already exists with slug: {existing_org.slug}")


if __name__ == "__main__":
    seed_organizations()
