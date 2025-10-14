from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from api.utils.loggers import create_logger
from api.utils.cache_manager import cached, cache_manager
from api.utils.database_optimizer import QueryOptimizer, monitor_query_performance

logger = create_logger(__name__)


@cached("total_count", ttl=300)  # Cache for 5 minutes
@monitor_query_performance
def total_row_count(model, db: Session, filters: Optional[Dict]=None):
    """Get total row count with caching and performance monitoring"""
    return model.count(
        db, 
        add_deleted=False, 
        filters=filters
    )


def off_set(page: int, size: int):
    return (page - 1) * size


def size_validator(size: int):
    if size < 0 or size > 100:
        return "page size must be between 0 and 100"
    return size


def page_urls(page: int, size: int, count: int, endpoint: str):
    paging = {}
    if (size + off_set(page, size)) >= count:
        paging["next"] = None
        if page > 1:
            paging["previous"] = f"{endpoint}?page={page-1}&size={size}"
        else:
            paging["previous"] = None
    else:
        paging["next"] = f"{endpoint}?page={page+1}&size={size}"
        if page > 1:
            paging["previous"] = f"{endpoint}?page={page-1}&size={size}"
        else:
            paging["previous"] = None

    return paging


@monitor_query_performance
def build_model_paginated_response(
    db: Session,
    model,
    endpoint: str,
    page: int=1, 
    size: int=10, 
    order: str='desc',
    sort_by: str='created_at',
    filters: Optional[Dict]=None,
    search_fields: Optional[Dict]=None,
    excludes: List[str]=[]
) -> dict:
    
    # Perform validation checks on page size 
    page_size = size
    if size > 100:
        page_size = 100
    elif size <= 0:
        size = 10
        
    # Do validation on page number
    page_number = 1 if page <= 0 else page
    
    # Build pagination items
    data, count = model.all(
        db,
        page=page_number,
        per_page=page_size,
        sort_by=sort_by,
        order=order,
    )
    items = [item.to_dict(excludes=excludes) for item in data]
    
    if filters:
        data, count = model.fetch_by_field(
            db, 
            page=page,
            per_page=page_size,
            sort_by=sort_by,
            order=order,
            **filters
        )
        items = [item.to_dict(excludes=excludes) for item in data]
    
    if search_fields:
        data, count = model.search(
            db,
            page=page,
            per_page=page_size,
            sort_by=sort_by,
            order=order,
            search_fields=search_fields
        )
        items = [item.to_dict(excludes=excludes) for item in data]
    
    # Generate total pages
    total_pages = (count // page_size) + 1 if count % page_size > 0 else (count // page_size)
    
    # Build page urls
    pointers = page_urls(
        page=page_number,
        size=page_size,
        count=count,
        endpoint=endpoint
    )
    
    response = {
        "status_code": 200,
        "success": True,
        "message": "Items fetched successfully",
        "pagination_data": {
            "current_page": page_number,
            "size": page_size,
            "total": count,
            "pages": total_pages,
            "previous_page": pointers["previous"],
            "next_page": pointers["next"],
        },
        "data": items,
    }

    return response


def build_paginated_response(
    items,
    endpoint: str,
    total: int,
    page: int=1, 
    size: int=10
) -> dict:
    
    # Perform validation checks on page size 
    page_size = size
    if size > 100:
        page_size = 100
    elif size <= 0:
        size = 10
    
    # Generate total pages
    total_pages = (total // page_size) + 1 if total % page_size > 0 else (total // page_size)
    
    # Do validation on page number
    page_number = 1 if page <= 0 or page > total_pages else page
    
    # Build page urls
    pointers = page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint=endpoint
    )
    
    response = {
        "status_code": 200,
        "success": True,
        "message": "Items fetched successfully",
        "pagination_data": {
            "current_page": page_number,
            "size": page_size,
            "total": total,
            "pages": total_pages,
            "previous_page": pointers["previous"],
            "next_page": pointers["next"],
        },
        "data": items,
    }

    return response


def paginate_query(query, page: int, per_page: int):
    count = query.count()
    offset = (page - 1) * per_page
    return query.offset(offset).limit(per_page).all(), count


@cached("optimized_pagination", ttl=180)  # Cache for 3 minutes
@monitor_query_performance
def optimized_paginate_query(
    query, 
    page: int, 
    per_page: int,
    use_optimized_count: bool = True
):
    """
    Optimized pagination with query optimization and caching
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        use_optimized_count: Whether to use optimized count query
        
    Returns:
        Tuple of (items, count)
    """
    # Use query optimizer for better performance
    optimized_query = QueryOptimizer.optimize_pagination_query(query, page, per_page)
    
    # Get count with optimization
    if use_optimized_count:
        # Use approximate count for better performance on large tables
        try:
            count = optimized_query.count()
        except Exception:
            # Fallback to regular count
            count = query.count()
    else:
        count = query.count()
    
    # Execute optimized query
    items = optimized_query.all()
    
    logger.debug(f"Optimized pagination: page={page}, per_page={per_page}, count={count}")
    return items, count


def get_pagination_metadata(
    page: int,
    per_page: int,
    total: int,
    endpoint: str
) -> Dict[str, any]:
    """
    Generate comprehensive pagination metadata
    
    Args:
        page: Current page number
        per_page: Items per page
        total: Total number of items
        endpoint: API endpoint for pagination links
        
    Returns:
        Dictionary with pagination metadata
    """
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    return {
        "current_page": page,
        "per_page": per_page,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "next_page": f"{endpoint}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "previous_page": f"{endpoint}?page={page - 1}&per_page={per_page}" if page > 1 else None,
        "first_page": f"{endpoint}?page=1&per_page={per_page}",
        "last_page": f"{endpoint}?page={total_pages}&per_page={per_page}" if total_pages > 0 else None,
        "page_range": {
            "start": (page - 1) * per_page + 1 if total > 0 else 0,
            "end": min(page * per_page, total)
        }
    }