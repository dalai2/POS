"""Simplify productos_pedido fields

Revision ID: 0013_simplify_productos_pedido
Revises: 0012_add_productos_pedido
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0013_simplify_productos_pedido'
down_revision = '0012_add_productos_pedido'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing columns that are not needed
    op.drop_column('productos_pedido', 'tiempo_entrega_dias')
    op.drop_column('productos_pedido', 'anticipo_porcentaje')
    op.drop_column('productos_pedido', 'anticipo_minimo')
    
    # Add new simplified columns
    op.add_column('productos_pedido', sa.Column('anticipo_sugerido', sa.Numeric(10, 2), nullable=True))
    op.add_column('productos_pedido', sa.Column('disponible', sa.Boolean(), nullable=True, default=True))


def downgrade():
    # Remove simplified columns
    op.drop_column('productos_pedido', 'disponible')
    op.drop_column('productos_pedido', 'anticipo_sugerido')
    
    # Add back old columns
    op.add_column('productos_pedido', sa.Column('tiempo_entrega_dias', sa.Integer(), nullable=True))
    op.add_column('productos_pedido', sa.Column('anticipo_porcentaje', sa.Numeric(5, 2), nullable=True))
    op.add_column('productos_pedido', sa.Column('anticipo_minimo', sa.Numeric(10, 2), nullable=True))