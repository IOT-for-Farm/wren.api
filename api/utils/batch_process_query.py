from typing import Type, Any, Optional, Generator
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Select

def batch_process_query(
    db: Session,
    model: Type[Any],
    batch_size: int = 200,
    query: Optional[Select] = None,
    # order_by_column: Optional[Any] = None,
    # start_from: Optional[Any] = None
):
    """
    Process database records in batches to avoid memory overload.
    
    Args:
        db: SQLAlchemy session
        model: SQLAlchemy model class
        batch_size: Number of records to fetch per batch (default: 200)
        query: Optional base query to use (if not provided, will select all from model)
        order_by_column: Column to order by (required for consistent pagination)
        start_from: Value to start from (for resuming processing)
    
    Yields:
        Lists of model instances in batches
    
    Example:
        for batch in batch_process(db, User, batch_size=500, order_by_column=User.id):
            process_batch(batch)
    """
    
    if query is None:
        query = db.query(model)
    
    # if order_by_column is None:
        # order_by_column = getattr(model, 'id')  # Default to id column if exists
    # order_by_column = getattr(model, 'updated_at')
    
    # if start_from is not None:
    #     query = query.filter(order_by_column > start_from)
    
    # query = query.order_by(order_by_column)
    
    # last_id = None
    last_updated = None
    
    while True:
        # Get a batch of records
        batch = query.limit(batch_size).all()
        
        if not batch:
            break  # No more records
            
        yield batch
        
        # last_id = getattr(batch[-1], order_by_column.name)
        
        # Update the query to get the next batch
        last_updated = getattr(batch[-1], 'updated_at')
        query = query.filter(model.updated_at < last_updated)
