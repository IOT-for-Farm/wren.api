from fastapi import Form, File, UploadFile
from typing import get_type_hints, Optional, List, Type
from pydantic import BaseModel
import inspect

def as_form_factory(model: Type[BaseModel]):
    """
    Returns a dependency function that parses form data into the given Pydantic model.
    """
    # Get model fields and types
    new_params = []
    for field_name, model_field in model.model_fields.items():
        field_type = model_field.annotation
        default = model_field.default if model_field.default is not None else None

        # Use File() for UploadFile, Form() for everything else
        if field_type == UploadFile or (
            hasattr(field_type, "__origin__") and field_type.__origin__ is Optional and UploadFile in field_type.__args__
        ):
            param = inspect.Parameter(
                field_name,
                inspect.Parameter.POSITIONAL_ONLY,
                default=File(default),
                annotation=field_type,
            )
        else:
            param = inspect.Parameter(
                field_name,
                inspect.Parameter.POSITIONAL_ONLY,
                default=Form(default),
                annotation=field_type,
            )
        new_params.append(param)

    # Create the function signature
    def as_form_func(*args, **kwargs):
        return model(*args, **kwargs)

    as_form_func.__signature__ = inspect.Signature(new_params)
    return as_form_func