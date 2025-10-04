import sys
import uvicorn, os, time
from typing import Optional
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  # required by google oauth
from config import config
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.db.database import create_database, get_db
from api.utils.loggers import create_logger
from api.utils.log_streamer import log_streamer
from api.utils.responses import success_response
from api.utils.telex_notification import TelexNotification
from api.v1.models import register_model_hooks
from api.v1.routes import v1_router
from api.utils.settings import settings
from api.utils.port_checker import find_free_port


create_database()

logger = create_logger(__name__, log_file='logs/error.log')
# performance_logger = create_logger(__name__, log_file='logs/performance.log')

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_model_hooks()
    yield

app = FastAPI(
    lifespan=lifespan,
    title='Wren API Documentation'
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

TEMP_DIR = './tmp/media'
os.makedirs(TEMP_DIR, exist_ok=True)
app.mount('/tmp/media', StaticFiles(directory=TEMP_DIR), name='tmp')

FILESTORAGE = f'./{config("FILESTORAGE")}'
os.makedirs(FILESTORAGE, exist_ok=True)
app.mount(f'/{config("FILESTORAGE")}', StaticFiles(directory=FILESTORAGE), name='files')

# Register Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    # allow_origins=settings.ALLOWED_ORIGINS,
    # allow_origins=[origin.strip() for origin in config('ALLOWED_ORIGINS').split(',')],
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log details after each request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Capture request start time
    start_time = time.time()

    # Process the request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time
    formatted_process_time = f"{process_time:.3f}s"
    
    response.headers["X-Process-Time"] = formatted_process_time

    # Capture request and response details
    client_ip = request.client.host
    method = request.method
    url = request.url.path
    status_code = response.status_code

    # Format the log string similar to your example
    log_string = (
        f"{client_ip} - \"{method} {url}\" {status_code} - {formatted_process_time}"
    )

    # Log the formatted string
    logger.info(log_string)
    
    # Send notification to Telex if an endpoint executes in more than 5 seconds
    # if process_time > 5:
    #     TelexNotification(webhook_id='01963c21-6423-7969-8860-a700224c36e1').send_notification(
    #         event_name='Performance Check',
    #         message=f"Performance issue on {method}-{url} {status_code}.\nThe endpoint is taking {formatted_process_time} to execute.\nCheck it out.",
    #         status='error',
    #         username='Wren Performance Reporter'
    #     )

    return response


# Load the router
app.include_router(v1_router)

@app.get("/", tags=["Home"])
async def root(request: Request) -> dict:
    return success_response(
        message="Welcome to API", 
        status_code=status.HTTP_200_OK
    )


@app.get("/logs", tags=["Home"])
async def stream_logs(
    lines: Optional[int] = Query(None), 
    log_file: Optional[str] = Query('app_logs.log')
) -> StreamingResponse:
    '''Endpoint to stream logs'''
    
    return StreamingResponse(log_streamer(f'logs/{log_file}', lines), media_type="text/event-stream")


# REGISTER EXCEPTION HANDLERS
@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    """HTTP exception handler"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    logger.error(f"HTTPException: {request.url.path} | {exc.status_code} | {exc.detail}", stacklevel=2)
    # logger.error(f"[ERROR] - An error occured | {exc}, {exc_type} {exc_obj} line {exc_tb.tb_lineno}", stacklevel=2)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "status_code": exc.status_code,
            "message": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    """Validation exception handler"""

    errors = [
        {
            "loc": error["loc"], 
            "msg": error["msg"], 
            "type": error["type"],
            # "msg": error["msg"].split(',')[-1].strip(), 
            # "detailed_message": f"{error['type'].capitalize()} {error['loc'][0]}: {error['loc'][1]}- {error['msg'].split(',')[-1].strip()}"
        } for error in exc.errors()
    ]
    
    # errors = [
    #     f"{error['type'].capitalize()} {error['loc'][0]}: {error['loc'][1]}- {error['msg'].split(',')[-1].strip()}"
    #     for error in exc.errors()
    # ]

    exc_type, exc_obj, exc_tb = sys.exc_info()
    logger.error(f"RequestValidationError: {request.url.path} | {errors}", stacklevel=2)
    logger.error(f"[ERROR] - An error occured | {exc}\n{exc_type}\n{exc_obj}\nLine {exc_tb.tb_lineno}", stacklevel=2)    

    return JSONResponse(
        status_code=422,
        content={
            "status": False,
            "status_code": 422,
            "message": "Invalid input",
            "errors": errors,
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception(request: Request, exc: IntegrityError):
    """Integrity error exception handlers"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    logger.error(f"Integrity error occured | {request.url.path} | 500", stacklevel=2)
    logger.error(f"[ERROR] - An error occured | {exc}\n{exc_type}\n{exc_obj}\nLine {exc_tb.tb_lineno}", stacklevel=2)
    
    # TelexNotification(webhook_id='01963c21-4279-7969-8d3c-0f7ce4ae824b').send_notification(
    #     event_name='Integrity error',
    #     message=f"[ERROR] - An error occured on {request.url.path}\n{exc}\n{exc_type}\n{exc_obj}\nLine {exc_tb.tb_lineno}",
    #     status='error',
    #     username='Wren Error Logger'
    # )
    
    if isinstance(exc.orig, UniqueViolation):
        constraint = getattr(exc.orig.diag, "constraint_name", None)
        
        return JSONResponse(
            status_code=400,
            content={
                "status": False,
                "status_code": 400,
                # "message": f"Unique constraint for key {constraint} violated",
                "message": f"{constraint.split('_')[-1].capitalize()} with the provided value already exists",
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "status_code": 500,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


@app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    """Other exception handlers"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    logger.error(f"Exception occured | {request.url.path} | 500", stacklevel=2)
    logger.error(f"[ERROR] - An error occured | {exc}\n{exc_type}\n{exc_obj}\nLine {exc_tb.tb_lineno}", stacklevel=2)    
    
    # TelexNotification(webhook_id='01963c21-4279-7969-8d3c-0f7ce4ae824b').send_notification(
    #     event_name='Exception',
    #     message=f"[ERROR] - An error occured on {request.url.path}\n{exc}\n{exc_type}\n{exc_obj}\nLine {exc_tb.tb_lineno}",
    #     status='error',
    #     username='Wren Error Logger'
    # )

    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "status_code": 500,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host='0.0.0.0',
        port=find_free_port(
            port=config('PORT', cast=int, default=7001),
            is_production=config('PYTHON_ENV') == "production"
        ), 
        reload=True,
        workers=4,
        reload_excludes=['logs/']
    )
