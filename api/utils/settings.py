import os
from pydantic_settings import BaseSettings
from config import config
from pathlib import Path


# Use this to build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """ Class to hold application's config values."""

    PYTHON_ENV: str = config("PYTHON_ENV")
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = config("REFRESH_TOKEN_EXPIRE_MINUTES")
    # ALLOWED_ORIGINS: list = config("ALLOWED_ORIGINS", cast=lambda v: [s.strip() for s in v.split(',')])
    # ALLOWED_ORIGINS: list = [origin.strip() for origin in config('ALLOWED_ORIGINS').split(',')]

    MAIL_USERNAME: str = config("MAIL_USERNAME")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD")
    MAIL_FROM: str = config("MAIL_FROM")
    MAIL_PORT: int = config("MAIL_PORT")
    MAIL_SERVER: str = config("MAIL_SERVER")
    MAIL_FROM_NAME: str = config("MAIL_FROM_NAME")

    # Database configurations
    DB_HOST: str = config("POSTGRES_HOST")
    DB_PORT: int = config("POSTGRES_PORT", cast=int)
    DB_USER: str = config("POSTGRES_USER")
    DB_PASSWORD: str = config("POSTGRES_PASSWORD")
    DB_NAME: str = config("POSTGRES_DB")
    DB_TYPE: str = config("DB_TYPE")
    DB_URL: str = config("POSTGRES_URI")
    
    TEMP_DIR: str = os.path.join(Path(__file__).resolve().parent.parent.parent, 'tmp', 'media') 

settings = Settings()
