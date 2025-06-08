import json
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.orm import Session
from sqlalchemy import event

from api.core.dependencies.celery.queues.general.tasks import save_activity_log
from api.core.dependencies.context import current_user_id


def get_field_differences(instance):
    # changes = []
    changes = {}
    
    for attr in instance.__table__.columns:
        history = get_history(instance, attr.name)
        
        if history.has_changes():
            old = history.deleted[0] if history.deleted else None
            new = history.added[0] if history.added else None
            
            if old != new:
                # changes.append(f"{attr.name}: '{old}' → '{new}'")
                # changes.append({
                #     f"{attr.name}": {
                #         "old": old,
                #         "new": new
                #     }
                # })
                
                changes[attr.name] = {
                    "old": old,
                    "new": new
                }
                
    # return "\n".join(changes) if changes else "No changes"
    return json.dumps(changes) if changes else json.dumps({})


def generate_description(instance, action: str):
    if action.lower() == "create":
        data = {c.name: getattr(instance, c.name) for c in instance.__table__.columns}
        return json.dumps(data, default=str)
    
    elif action.lower() == "update":
        return get_field_differences(instance)
    
    elif action.lower() == "delete":
        return f"Deleted record: {instance.__tablename__} with id={instance.id}"


def register_activity_logging(Model, db: Session):
    
    def log_create(mapper, connection, target):
        if getattr(target, "_disable_activity_logging", False):
            return

        action = "create"

        log_data = {
            "organization_id": getattr(target, "organization_id", None),
            "user_id": current_user_id.get(),
            "model_name": target.__tablename__,
            "model_id": str(target.id),
            "action": action.lower(),
            "description": generate_description(target, action),
        }

        # Dispatch to Celery instead of writing synchronously
        save_activity_log.delay(log_data)
        
    def log_update(mapper, connection, target):
        if getattr(target, "_disable_activity_logging", False):
            return

        action = "update"

        log_data = {
            "organization_id": getattr(target, "organization_id", None),
            "user_id": current_user_id.get(),
            "model_name": target.__tablename__,
            "model_id": str(target.id),
            "action": action.lower(),
            "description": generate_description(target, action),
        }

        # Dispatch to Celery instead of writing synchronously
        save_activity_log.delay(log_data)

    def log_delete(mapper, connection, target):
        if getattr(target, "_disable_activity_logging", False):
            return

        log_data = {
            "organization_id": getattr(target, "organization_id", None),
            "user_id": current_user_id.get(),
            "model_name": target.__tablename__,
            "model_id": str(target.id),
            "action": "delete",
            "description": generate_description(target, "delete"),
        }
        
        save_activity_log.delay(log_data)
        
    event.listen(Model, "after_insert", log_create)
    event.listen(Model, "after_update", log_update)
    event.listen(Model, "after_delete", log_delete)
