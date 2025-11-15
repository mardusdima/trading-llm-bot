"""Initial schema with TimescaleDB hypertables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=True),
        sa.Column('order_id', sa.String(), nullable=True),
        sa.Column('side', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trades_timestamp', 'trades', ['timestamp'], unique=False)
    op.create_index('ix_trades_symbol', 'trades', ['symbol'], unique=False)

    # Create candles table
    op.create_table(
        'candles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('open', sa.Float(), nullable=True),
        sa.Column('high', sa.Float(), nullable=True),
        sa.Column('low', sa.Float(), nullable=True),
        sa.Column('close', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('timeframe', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_candles_exchange_symbol_time', 'candles', ['exchange', 'symbol', 'timestamp'], unique=False)
    op.create_index('ix_candles_timestamp', 'candles', ['timestamp'], unique=False)

    # Create tickers table
    op.create_table(
        'tickers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('bid', sa.Float(), nullable=True),
        sa.Column('ask', sa.Float(), nullable=True),
        sa.Column('info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tickers_exchange_symbol_time', 'tickers', ['exchange', 'symbol', 'timestamp'], unique=False)
    op.create_index('ix_tickers_timestamp', 'tickers', ['timestamp'], unique=False)

    # Create orderbooks table
    op.create_table(
        'orderbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('bids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('asks', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_orderbooks_exchange_symbol_time', 'orderbooks', ['exchange', 'symbol', 'timestamp'], unique=False)
    op.create_index('ix_orderbooks_timestamp', 'orderbooks', ['timestamp'], unique=False)

    # Convert to TimescaleDB hypertables
    op.execute("SELECT create_hypertable('candles', 'timestamp', if_not_exists => TRUE);")
    op.execute("SELECT create_hypertable('tickers', 'timestamp', if_not_exists => TRUE);")
    op.execute("SELECT create_hypertable('orderbooks', 'timestamp', if_not_exists => TRUE);")


def downgrade() -> None:
    # Drop hypertables first (TimescaleDB will handle this)
    op.execute("SELECT drop_hypertable('candles', if_exists => TRUE);")
    op.execute("SELECT drop_hypertable('tickers', if_exists => TRUE);")
    op.execute("SELECT drop_hypertable('orderbooks', if_exists => TRUE);")
    
    # Drop tables
    op.drop_index('ix_orderbooks_timestamp', table_name='orderbooks')
    op.drop_index('ix_orderbooks_exchange_symbol_time', table_name='orderbooks')
    op.drop_table('orderbooks')
    
    op.drop_index('ix_tickers_timestamp', table_name='tickers')
    op.drop_index('ix_tickers_exchange_symbol_time', table_name='tickers')
    op.drop_table('tickers')
    
    op.drop_index('ix_candles_timestamp', table_name='candles')
    op.drop_index('ix_candles_exchange_symbol_time', table_name='candles')
    op.drop_table('candles')
    
    op.drop_index('ix_trades_symbol', table_name='trades')
    op.drop_index('ix_trades_timestamp', table_name='trades')
    op.drop_table('trades')

