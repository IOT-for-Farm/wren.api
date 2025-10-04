import sys
import pathlib
from datetime import datetime, timedelta

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.event import Event, EventAttendee
from api.v1.models.organization import Organization
from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager


def seed_events():
    '''Seed events and event attendees'''
    
    with get_db_with_ctx_manager() as db:
        # Get required dependencies
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
    
    admin_user = User.fetch_one_by_field(
        db=db,
        throw_error=False,
        email="admin@greentrac.com"
    )
    
    users = User.fetch_by_field(
        db=db,
        paginate=False
    )[1]  # Get the results, not the query
    
    if not greentrac_org or not admin_user:
        print("Required dependencies not found. Please run seed_organizations.py and seed_users.py first.")
        return
    
    # Create events for different organizations
    events_data = [
        {
            "organization_id": greentrac_org.id,
            "title": "Solar Energy Workshop 2024",
            "description": "Learn about the latest trends in solar energy technology and installation best practices. This workshop is perfect for both beginners and professionals in the renewable energy sector.",
            "slug": "solar-energy-workshop-2024",
            "visibility": "public",
            "event_type": "workshop",
            "start": datetime.now() + timedelta(days=30),
            "end": datetime.now() + timedelta(days=30, hours=4),
            "location": "GreenTrac Conference Center, Lagos",
            "location_type": "physical",
            "allow_rsvp": True,
            "attendee_limit": 50,
            "is_recurring": False,
            "recurrence_rule": None,
            "creator_id": admin_user.id,
            "additional_info": {
                "agenda": [
                    "9:00 AM - Registration and Welcome",
                    "9:30 AM - Solar Technology Overview",
                    "11:00 AM - Installation Best Practices",
                    "12:30 PM - Lunch Break",
                    "2:00 PM - Case Studies and Q&A",
                    "4:00 PM - Closing Remarks"
                ],
                "speakers": ["Dr. Solar Expert", "Mr. Installation Pro"],
                "cost": "Free",
                "certificate": "Available upon completion"
            }
        },
        {
            "organization_id": greentrac_org.id,
            "title": "Weekly Green Tech Meetup",
            "description": "Join us every week for discussions about green technology, sustainability practices, and networking with like-minded professionals.",
            "slug": "weekly-green-tech-meetup",
            "visibility": "public",
            "event_type": "meetup",
            "start": datetime.now() + timedelta(days=7),
            "end": datetime.now() + timedelta(days=7, hours=2),
            "location": "Zoom Meeting Room",
            "location_type": "virtual",
            "allow_rsvp": True,
            "attendee_limit": 100,
            "is_recurring": True,
            "recurrence_rule": "FREQ=WEEKLY;BYDAY=FR",
            "creator_id": admin_user.id,
            "additional_info": {
                "meeting_link": "https://zoom.us/j/123456789",
                "topics": ["Renewable Energy", "Sustainable Business", "Green Innovation"],
                "cost": "Free",
                "format": "Interactive discussion"
            }
        },
        {
            "organization_id": ecofriendly_org.id,
            "title": "Environmental Impact Assessment Training",
            "description": "Comprehensive training on conducting environmental impact assessments for various projects. Perfect for environmental consultants and project managers.",
            "slug": "environmental-impact-assessment-training",
            "visibility": "public",
            "event_type": "training",
            "start": datetime.now() + timedelta(days=45),
            "end": datetime.now() + timedelta(days=47),
            "location": "EcoFriendly Training Center, Abuja",
            "location_type": "physical",
            "allow_rsvp": True,
            "attendee_limit": 25,
            "is_recurring": False,
            "recurrence_rule": None,
            "creator_id": admin_user.id,
            "additional_info": {
                "duration": "3 days",
                "schedule": "9:00 AM - 5:00 PM daily",
                "materials": "Provided",
                "certification": "EIA Professional Certificate",
                "cost": "NGN 150,000",
                "prerequisites": "Basic environmental knowledge"
            }
        },
        {
            "organization_id": greentrac_org.id,
            "title": "Product Launch: New Solar Inverter Series",
            "description": "Join us for the official launch of our new high-efficiency solar inverter series. Learn about the features, benefits, and pricing.",
            "slug": "solar-inverter-launch-2024",
            "visibility": "public",
            "event_type": "product_launch",
            "start": datetime.now() + timedelta(days=14),
            "end": datetime.now() + timedelta(days=14, hours=2),
            "location": "GreenTrac Showroom, Lagos",
            "location_type": "physical",
            "allow_rsvp": True,
            "attendee_limit": 75,
            "is_recurring": False,
            "recurrence_rule": None,
            "creator_id": admin_user.id,
            "additional_info": {
                "products": ["Solar Inverter 5kW", "Solar Inverter 10kW"],
                "special_offers": "20% discount for early orders",
                "refreshments": "Provided",
                "parking": "Free parking available",
                "dress_code": "Business casual"
            }
        }
    ]
    
    created_events = []
    
    for event_data in events_data:
        existing_event = Event.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug=event_data['slug'],
            organization_id=event_data['organization_id']
        )
        
        if not existing_event:
            new_event = Event.create(
                db=db,
                **event_data
            )
            created_events.append(new_event)
            print(f"Event '{new_event.title}' created")
            
            # Create event attendees (invite some users)
            num_attendees = min(5, len(users))
            selected_users = users[:num_attendees]
            
            for i, user in enumerate(selected_users):
                attendee_data = {
                    "event_id": new_event.id,
                    "user_id": user.id,
                    "email": user.email,
                    "name": f"{user.first_name} {user.last_name}",
                    "phone": user.phone_number,
                    "phone_country_code": user.phone_country_code,
                    "status": "accepted" if i < 3 else "invited",  # First 3 are accepted, others invited
                    "respnded_at": datetime.now() if i < 3 else None
                }
                
                new_attendee = EventAttendee.create(
                    db=db,
                    **attendee_data
                )
                print(f"  - Attendee added: {user.email} ({new_attendee.status})")
        else:
            print(f"Event '{existing_event.title}' already exists")
    
    print(f"Total events created: {len(created_events)}")


if __name__ == "__main__":
    seed_events()
