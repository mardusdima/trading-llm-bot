"""Add portfolio and position tables

Revision ID: 002_portfolio
Revises: 001_initial
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_portfolio'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('avg_entry_price', sa.Float(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('entry_timestamp', sa.DateTime(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_positions_exchange_symbol', 'positions', ['exchange', 'symbol'], unique=False)
    op.create_index('ix_positions_symbol', 'positions', ['symbol'], unique=False)

    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('total_pnl', sa.Float(), nullable=True),
        sa.Column('realized_pnl', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('peak_value', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('exchange')
    )


def downgrade() -> None:
    op.drop_table('portfolios')
    op.drop_index('ix_positions_symbol', table_name='positions')
    op.drop_index('ix_positions_exchange_symbol', table_name='positions')
    op.drop_table('positions')

