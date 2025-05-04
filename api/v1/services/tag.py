from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.tag import Tag
from api.v1.schemas import tag as tag_schemas


logger = create_logger(__name__)

class TagService:
    pass
