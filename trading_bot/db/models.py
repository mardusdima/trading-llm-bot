from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    order_id = Column(String)
    side = Column(String)
    amount = Column(Float)
    price = Column(Float)
    timestamp = Column(DateTime)
    status = Column(String)
    # TODO: Add TimescaleDB-specific features for timeseries efficiency

class Candle(Base):
    __tablename__ = 'candles'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    timeframe = Column(String, default="1m")
    # For TimescaleDB: set up hypertable on timestamp
    __table_args__ = (Index('ix_candles_exchange_symbol_time', 'exchange', 'symbol', 'timestamp'),)

class Ticker(Base):
    __tablename__ = 'tickers'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    info = Column(JSON)  # raw API response fragment
    __table_args__ = (Index('ix_tickers_exchange_symbol_time', 'exchange', 'symbol', 'timestamp'),)

class OrderBook(Base):
    __tablename__ = 'orderbooks'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    bids = Column(JSON) # topN depth json
    asks = Column(JSON)
    info = Column(JSON)  # full raw book/metadata
    __table_args__ = (Index('ix_orderbooks_exchange_symbol_time', 'exchange', 'symbol', 'timestamp'),)
