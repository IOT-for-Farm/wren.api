import sys
import pathlib
import hashlib
import secrets

from api.v1.services.auth import AuthService

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager


def seed_users():
    '''Seed users'''
    
    with get_db_with_ctx_manager() as db:
        users = [
            {
                "email": "admin@greentrac.com",
                "password": AuthService.hash_secret("admin123"),
                "first_name": "Admin",
                "last_name": "User",
                "username": "admin",
                "phone_number": "8123456789",
                "phone_country_code": "+234",
                "city": "Lagos",
                "state": "Lagos",
                "country": "Nigeria",
                "bio": "System administrator",
                "address": "123 Admin Street, Lagos, Nigeria",
                "is_active": True,
                "is_superuser": True
            },
            {
                "email": "john.doe@greentrac.com",
                "password": AuthService.hash_secret("password123"),
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "phone_number": "8123456780",
                "phone_country_code": "+234",
                "city": "Abuja",
                "state": "FCT",
                "country": "Nigeria",
                "bio": "Software Developer",
                "address": "456 Developer Avenue, Abuja, Nigeria",
                "is_active": True,
                "is_superuser": False
            },
            {
                "email": "jane.smith@greentrac.com",
                "password": AuthService.hash_secret("password123"),
                "first_name": "Jane",
                "last_name": "Smith",
                "username": "janesmith",
                "phone_number": "8123456781",
                "phone_country_code": "+234",
                "city": "Port Harcourt",
                "state": "Rivers",
                "country": "Nigeria",
                "bio": "Project Manager",
                "address": "789 Manager Road, Port Harcourt, Nigeria",
                "is_active": True,
                "is_superuser": False
            },
            {
                "email": "mike.wilson@greentrac.com",
                "password": AuthService.hash_secret("password123"),
                "first_name": "Mike",
                "last_name": "Wilson",
                "username": "mikewilson",
                "phone_number": "8123456782",
                "phone_country_code": "+234",
                "city": "Ibadan",
                "state": "Oyo",
                "country": "Nigeria",
                "bio": "Marketing Specialist",
                "address": "321 Marketing Street, Ibadan, Nigeria",
                "is_active": True,
                "is_superuser": False
            },
            {
                "email": "sarah.johnson@greentrac.com",
                "password": AuthService.hash_secret("password123"),
                "first_name": "Sarah",
                "last_name": "Johnson",
                "username": "sarahjohnson",
                "phone_number": "8123456783",
                "phone_country_code": "+234",
                "city": "Kano",
                "state": "Kano",
                "country": "Nigeria",
                "bio": "Sales Representative",
                "address": "654 Sales Boulevard, Kano, Nigeria",
                "is_active": True,
                "is_superuser": False
            }
        ]
        
        for user_data in users:
            existing_user = User.fetch_one_by_field(
                db=db, 
                throw_error=False,
                email=user_data['email']
            )
            
            if not existing_user:
                new_user = User.create(
                    db=db,
                    **user_data
                )
                print(f"User {new_user.email} created")
            else:
                print(f"User {existing_user.email} already exists")


if __name__ == "__main__":
    seed_users()
