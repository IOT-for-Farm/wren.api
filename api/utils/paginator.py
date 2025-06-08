from typing import Dict, List, Optional
from sqlalchemy.orm import Session


def total_row_count(model, db: Session, filters: Optional[Dict]=None):
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