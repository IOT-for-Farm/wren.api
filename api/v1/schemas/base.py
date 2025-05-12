from typing import Any, List, Optional
from pydantic import BaseModel

from api.v1.models import *
# from api.utils.helpers import generate_pydantic_schema


# UserSchema = generate_pydantic_schema(User, exclude_fields=["password", "is_superuser"])
# OrganizationSchema = generate_pydantic_schema(Organization)
# OrganizationMemberSchema = generate_pydantic_schema(OrganizationMember)
# OrganizationRoleSchema = generate_pydantic_schema(OrganizationRole)
# ContactInfoSchema = generate_pydantic_schema(ContactInfo)
# LocationSchema = generate_pydantic_schema(Location)
# DepartmentSchema = generate_pydantic_schema(Department)
# DepartmentMemberSchema = generate_pydantic_schema(DepartmentMember)
# FileSchema = generate_pydantic_schema(File)
# FormResponseSchema = generate_pydantic_schema(FormResponse)
# FormSchema = generate_pydantic_schema(Form)
# ApikeySchema = generate_pydantic_schema(Apikey, exclude_fields=['key_hash'])


class AdditionalInfoSchema(BaseModel):
    key: str
    value: Any    
    
class DeleteMultiple(BaseModel):
    ids: List[str]
