from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Literal, Optional
import os

class Settings(BaseSettings):
    # Environment
    ENV: Literal['dev', 'staging', 'prod'] = Field(default='dev', description='Environment')
    LOG_LEVEL: str = Field(default='INFO', description='Logging level')
    
    # Database
    DATABASE_URL: str = Field(
        default='postgresql://postgres:postgres@localhost:5432/tradingbot',
        description='PostgreSQL DB URL'
    )
    
    # Redis
    REDIS_URL: str = Field(
        default='redis://localhost:6379/0',
        description='Redis connection string'
    )
    
    # Exchange API Keys (optional, can be set per exchange)
    BINANCE_API_KEY: Optional[str] = Field(default=None, description='Binance API key')
    BINANCE_API_SECRET: Optional[str] = Field(default=None, description='Binance API secret')
    
    ALPACA_API_KEY: Optional[str] = Field(default=None, description='Alpaca API key')
    ALPACA_API_SECRET: Optional[str] = Field(default=None, description='Alpaca API secret')
    
    COINBASE_API_KEY: Optional[str] = Field(default=None, description='Coinbase API key')
    COINBASE_API_SECRET: Optional[str] = Field(default=None, description='Coinbase API secret')
    COINBASE_PASSPHRASE: Optional[str] = Field(default=None, description='Coinbase passphrase')
    
    # Trading Settings
    PAPER_TRADING: bool = Field(default=True, description='Enable paper trading mode')
    MAX_POSITION_SIZE: float = Field(default=1000.0, description='Max position size in USD')
    MAX_DRAWDOWN_PCT: float = Field(default=10.0, description='Max drawdown percentage')
    STOP_LOSS_PCT: float = Field(default=2.0, description='Stop loss percentage')
    POSITION_SIZE_PCT: float = Field(default=10.0, description='Position size as % of portfolio')
    
    # Order Execution
    MAX_ORDER_RETRIES: int = Field(default=3, description='Max order retry attempts')
    RETRY_DELAY: float = Field(default=1.0, description='Retry delay in seconds')
    
    # Symbols
    SYMBOLS_CRYPTO: str = Field(default='BTC/USDT,ETH/USDT', description='Crypto symbols to trade')
    SYMBOLS_STOCKS: str = Field(default='AAPL,MSFT', description='Stock symbols to trade')
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    @validator('MAX_DRAWDOWN_PCT', 'STOP_LOSS_PCT', 'POSITION_SIZE_PCT')
    def validate_percentage(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = 'ignore'  # Ignore extra env vars

# Global settings instance
settings = Settings()
