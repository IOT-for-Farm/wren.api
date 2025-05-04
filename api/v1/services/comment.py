from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.comment import Comment
from api.v1.schemas import comment as comment_schemas


logger = create_logger(__name__)

class CommentService:
    pass
