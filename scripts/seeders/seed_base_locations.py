import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.location import BaseLocation
from api.db.database import get_db_with_ctx_manager


def seed_base_locations():
    '''Seed base locations (continents, countries, states, cities)'''
    
    with get_db_with_ctx_manager() as db:
        locations = [
            # Continents
            {
                "location_name": "Africa",
                "location_type": "continent",
                "parent_id": None,
                "parent_name": None,
                "parent_type": None,
                "description": "The African continent",
                "longitude": 20.0,
                "latitude": 0.0,
                "currency_code": None,
                "short_code": "AF",
                "emoji": "🌍",
                "emoji_code": "earth_africa"
            },
            {
                "location_name": "North America",
                "location_type": "continent",
                "parent_id": None,
                "parent_name": None,
                "parent_type": None,
                "description": "The North American continent",
                "longitude": -100.0,
                "latitude": 45.0,
                "currency_code": None,
                "short_code": "NA",
                "emoji": "🌎",
                "emoji_code": "earth_americas"
            },
            
            # Countries
            {
                "location_name": "Nigeria",
                "location_type": "country",
                "parent_id": None,  # Will be set after continent is created
                "parent_name": "Africa",
                "parent_type": "continent",
                "description": "Federal Republic of Nigeria",
                "longitude": 8.0,
                "latitude": 10.0,
                "currency_code": "NGN",
                "short_code": "NG",
                "emoji": "🇳🇬",
                "emoji_code": "flag-ng"
            },
            {
                "location_name": "United States",
                "location_type": "country",
                "parent_id": None,  # Will be set after continent is created
                "parent_name": "North America",
                "parent_type": "continent",
                "description": "United States of America",
                "longitude": -95.0,
                "latitude": 39.0,
                "currency_code": "USD",
                "short_code": "US",
                "emoji": "🇺🇸",
                "emoji_code": "flag-us"
            },
            {
                "location_name": "United Kingdom",
                "location_type": "country",
                "parent_id": None,
                "parent_name": "Europe",
                "parent_type": "continent",
                "description": "United Kingdom of Great Britain and Northern Ireland",
                "longitude": -3.0,
                "latitude": 55.0,
                "currency_code": "GBP",
                "short_code": "GB",
                "emoji": "🇬🇧",
                "emoji_code": "flag-gb"
            },
            
            # States/Provinces
            {
                "location_name": "Lagos",
                "location_type": "state",
                "parent_id": None,  # Will be set after country is created
                "parent_name": "Nigeria",
                "parent_type": "country",
                "description": "Lagos State",
                "longitude": 3.4,
                "latitude": 6.5,
                "currency_code": "NGN",
                "short_code": "LA",
                "emoji": "🏙️",
                "emoji_code": "cityscape"
            },
            {
                "location_name": "Abuja",
                "location_type": "state",
                "parent_id": None,  # Will be set after country is created
                "parent_name": "Nigeria",
                "parent_type": "country",
                "description": "Federal Capital Territory",
                "longitude": 7.5,
                "latitude": 9.1,
                "currency_code": "NGN",
                "short_code": "FC",
                "emoji": "🏛️",
                "emoji_code": "classical_building"
            },
            {
                "location_name": "California",
                "location_type": "state",
                "parent_id": None,  # Will be set after country is created
                "parent_name": "United States",
                "parent_type": "country",
                "description": "State of California",
                "longitude": -119.0,
                "latitude": 37.0,
                "currency_code": "USD",
                "short_code": "CA",
                "emoji": "🌴",
                "emoji_code": "palm_tree"
            },
            
            # Cities
            {
                "location_name": "Lagos City",
                "location_type": "city",
                "parent_id": None,  # Will be set after state is created
                "parent_name": "Lagos",
                "parent_type": "state",
                "description": "Lagos City, Lagos State",
                "longitude": 3.4,
                "latitude": 6.5,
                "currency_code": "NGN",
                "short_code": "LOS",
                "emoji": "🏙️",
                "emoji_code": "cityscape"
            },
            {
                "location_name": "Abuja City",
                "location_type": "city",
                "parent_id": None,  # Will be set after state is created
                "parent_name": "Abuja",
                "parent_type": "state",
                "description": "Abuja City, Federal Capital Territory",
                "longitude": 7.5,
                "latitude": 9.1,
                "currency_code": "NGN",
                "short_code": "ABJ",
                "emoji": "🏛️",
                "emoji_code": "classical_building"
            },
            {
                "location_name": "San Francisco",
                "location_type": "city",
                "parent_id": None,  # Will be set after state is created
                "parent_name": "California",
                "parent_type": "state",
                "description": "San Francisco, California",
                "longitude": -122.4,
                "latitude": 37.8,
                "currency_code": "USD",
                "short_code": "SFO",
                "emoji": "🌉",
                "emoji_code": "bridge_at_night"
            }
        ]
    
    # Create a mapping to store created locations for parent references
    created_locations = {}
    
    for location_data in locations:
        # Skip parent_id for now, we'll set it after creating parent locations
        location_data_copy = location_data.copy()
        parent_id = location_data_copy.pop('parent_id', None)
        
        existing_location = BaseLocation.fetch_one_by_field(
            db=db, 
            throw_error=False,
            location_name=location_data['location_name'],
            location_type=location_data['location_type']
        )
        
        if not existing_location:
            new_location = BaseLocation.create(
                db=db,
                **location_data_copy
            )
            created_locations[f"{location_data['location_name']}_{location_data['location_type']}"] = new_location.id
            print(f"BaseLocation {new_location.location_name} ({new_location.location_type}) created")
        else:
            created_locations[f"{location_data['location_name']}_{location_data['location_type']}"] = existing_location.id
            print(f"BaseLocation {existing_location.location_name} ({existing_location.location_type}) already exists")
    
    # Now update parent_id references
    for location_data in locations:
        if location_data.get('parent_name') and location_data.get('parent_type'):
            parent_key = f"{location_data['parent_name']}_{location_data['parent_type']}"
            if parent_key in created_locations:
                # Find the location and update its parent_id
                location = BaseLocation.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    location_name=location_data['location_name'],
                    location_type=location_data['location_type']
                )
                if location and not location.parent_id:
                    location.parent_id = created_locations[parent_key]
                    db.commit()
                    print(f"Updated parent_id for {location.location_name} to {parent_key}")


if __name__ == "__main__":
    seed_base_locations()
