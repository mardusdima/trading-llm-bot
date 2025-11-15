from pydantic import BaseSettings, Field
from typing import Literal
import os

class Settings(BaseSettings):
    ENV: Literal['dev', 'staging', 'prod'] = Field('dev', description='Environment')
    API_KEY: str = Field(..., description='API key')
    API_SECRET: str = Field(..., description='API secret')
    DATABASE_URL: str = Field(..., description='PostgreSQL DB URL')
    REDIS_URL: str = Field(..., description='Redis connection string')
    LOG_LEVEL: str = Field('INFO', description='Logging level')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()
