import random
from fastapi import Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Type, Any
from pydantic import BaseModel, create_model
from requests import Session
from sqlalchemy.inspection import inspect
from googletrans import Translator

from api.v1.models.organization import Organization
from api.v1.models.user import User
from api.v1.schemas.base import AdditionalInfoSchema


def generate_logo_url(name: str):
    return f"https://ui-avatars.com/api/?name={name}"


def generate_pydantic_schema(
    sa_model, 
    exclude_fields: Optional[List]=None, 
    name_suffix: str="Schema"
) -> Type[BaseModel]:
    
    default_excluded_fields = ["is_deleted"]
    exclude_fields = exclude_fields+default_excluded_fields if exclude_fields else default_excluded_fields
    mapper = inspect(sa_model)
    fields = {
        column.key: (column.type.python_type, ...)
        for column in mapper.columns
        if column.key not in exclude_fields
    }

    return create_model(sa_model.__name__ + name_suffix, **fields)


def generate_unique_id(
    db: Optional[Session] = None,
    name: Optional[str]=None, 
    organization_id: Optional[str]=None, 
    passes: int = 6
):
    '''Function to geenrate a random unique id
    
    Args:
        name Optional(str): Prefrably the organization name but can be anything
        organization_id Optional(str): ID of the organization you want to create unique id for
        passes (int): Amount of randomized numbers you want generated in the id. Generates minimum of 5 and maxiumum of 10. This number will be added
        to the ASCII value of the first 3 chaacters in the name
    '''
    
    if not name and not organization_id:
        raise ValueError('Both name and organization id cannot be missing')
    
    if name and organization_id:
        raise ValueError('Both name and organization id cannot be present')
    
    if organization_id and not db:
        raise ValueError('When organizationid is provided, a valid db session is required')
    
    if name:
        first_three_letters = name[:3].upper()
    
    if organization_id and db:
        organization = Organization.fetch_by_id(db, organization_id)
        first_three_letters = organization.name[:3].upper()
    
    # Convert first three letter to ascii
    ascii_str = ''.join(str(ord(char)) for char in first_three_letters)
    ascii_int = int(ascii_str)
    
    # Determine number of number passes for the loop
    if passes < 5:
        passes = 5
    elif passes > 10:
        passes = 10
        
    number_string = ""
    
    for _ in range(passes):
        random_number = f'{random.randint(0, 9)}'
        number_string +=random_number
    
    # Generate unique id
    id_number = ascii_int + int(number_string)
    unique_id = f"{first_three_letters}{id_number}"
        
    return unique_id


def format_additional_info_create(additional_info: List[AdditionalInfoSchema]):
    '''Function to help format additional info for create endpoints into JSON format'''
    
    return {info.key: info.value for info in additional_info}
    

def format_additional_info_update(additional_info: List[AdditionalInfoSchema], model_instance):
    '''Function to help format additional info for update endpoints for an existing object'''
    
    current_additional_info_dict_copy = model_instance.additional_info.copy()
    for info in additional_info:
        current_additional_info_dict_copy[info.key] = info.value
    
    print(current_additional_info_dict_copy)
    return current_additional_info_dict_copy


def check_user_is_owner(user_id: str, model_instance, user_fk_name: str):
    """
    Check if the user has permission to access a resource based on a foreign key field.
    user_id is not necessariyl going to be a id field on the User table. It could be a
    id field on any table that mimicks user in a way eg supplier, customer, business partner.
    """
    
    resource_user_id = getattr(model_instance, user_fk_name, None)
    
    if resource_user_id is None:
        raise HTTPException(500, f"Model `{model_instance.__name__}` does not have attribute `{user_fk_name}`")
    
    if user_id != resource_user_id:
        raise HTTPException(403, 'You do not have permission to access this resource')


async def translate_text(text: str, destination_language: str='fr'):
    '''Function to help translate text with googletrans package'''
    
    translator = Translator()
    result = await translator.translate(text, dest=destination_language)
    return result.text
