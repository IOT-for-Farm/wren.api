import json
from sqlalchemy.orm.attributes import get_history


def get_field_differences(instance):
    changes = []
    
    for attr in instance.__table__.columns:
        history = get_history(instance, attr.name)
        
        if history.has_changes():
            old = history.deleted[0] if history.deleted else None
            new = history.added[0] if history.added else None
            
            if old != new:
                changes.append(f"{attr.name}: '{old}' → '{new}'")
                
    return "\n".join(changes) if changes else "No changes"


def generate_description(instance, action: str):
    if action.upper() == "CREATE":
        data = {c.name: getattr(instance, c.name) for c in instance.__table__.columns}
        return f"Created with data: {json.dumps(data, default=str)}"
    
    elif action.upper() == "UPDATE":
        return f"Updated fields:\n{get_field_differences(instance)}"
    
    elif action.upper() == "DELETE":
        return f"Deleted record: {instance.__tablename__} with id={instance.id}"
