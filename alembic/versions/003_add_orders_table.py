"""Add orders table for order management

Revision ID: 003_orders
Revises: 002_portfolio
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_orders'
down_revision = '002_portfolio'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('exchange_order_id', sa.String(), nullable=True),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('order_type', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('filled_amount', sa.Float(), nullable=True),
        sa.Column('average_fill_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_orders_exchange_symbol_status', 'orders', ['exchange', 'symbol', 'status'], unique=False)
    op.create_index('ix_orders_exchange_order_id', 'orders', ['exchange_order_id'], unique=False)
    op.create_index('ix_orders_symbol', 'orders', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_orders_symbol', table_name='orders')
    op.drop_index('ix_orders_exchange_order_id', table_name='orders')
    op.drop_index('ix_orders_exchange_symbol_status', table_name='orders')
    op.drop_table('orders')

