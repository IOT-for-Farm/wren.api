from fastapi import Form
from pydantic import BaseModel
from typing import Type, Any, Dict, Union

def as_form(cls: Type[BaseModel]) -> Type[BaseModel]:
    """
    Converts a Pydantic model to accept form data instead of JSON.
    Usage:
    @app.post("/login")
    async def login(form_data: LoginForm = Depends(LoginForm.as_form)):
    """
    
    form_params = []
    for field_name, field in cls.model_fields.items():
        annotation = field.annotation
        default = field.default if field.default is not None else ...
        
        # Handle Optional fields
        if hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
            if type(None) in annotation.__args__:
                annotation = annotation.__args__[0]
                default = Form(default=None)
        
        form_params.append(
            (field_name, annotation, Form(default=default))
        )

    # Dynamically create a new model with Form fields
    return type(
        cls.__name__,
        (cls,),
        {
            "__annotations__": {name: typ for name, typ, _ in form_params},
            **{name: val for name, _, val in form_params}
        }
    )