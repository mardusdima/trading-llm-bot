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

class Position(Base):
    __tablename__ = 'positions'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)
    side = Column(String, nullable=False)  # 'buy' or 'sell'
    entry_timestamp = Column(DateTime, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    __table_args__ = (Index('ix_positions_exchange_symbol', 'exchange', 'symbol'),)

class Portfolio(Base):
    __tablename__ = 'portfolios'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False, unique=True)
    initial_capital = Column(Float, nullable=False, default=10000.0)
    current_value = Column(Float, nullable=False, default=10000.0)
    total_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    peak_value = Column(Float, nullable=False, default=10000.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    exchange_order_id = Column(String, nullable=True, index=True)  # Order ID from exchange
    symbol = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)  # 'buy' or 'sell'
    order_type = Column(String, nullable=False)  # 'market', 'limit', etc.
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # None for market orders
    status = Column(String, nullable=False, default='pending')  # pending, filled, partial, canceled, rejected
    filled_amount = Column(Float, default=0.0)
    average_fill_price = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    error_message = Column(String, nullable=True)
    __table_args__ = (Index('ix_orders_exchange_symbol_status', 'exchange', 'symbol', 'status'),)
