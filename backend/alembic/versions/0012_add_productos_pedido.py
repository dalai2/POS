"""Add productos_pedido tables

Revision ID: 0012_add_productos_pedido
Revises: 0011_remove_sku_barcode_keep_codigo
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0012_add_productos_pedido'
down_revision = '0011_remove_sku_barcode_keep_codigo'
branch_labels = None
depends_on = None


def upgrade():
    # Create productos_pedido table
    op.create_table('productos_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('modelo', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('quilataje', sa.String(length=20), nullable=True),
        sa.Column('talla', sa.String(length=20), nullable=True),
        sa.Column('peso_gramos', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('precio', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('costo', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('tiempo_entrega_dias', sa.Integer(), nullable=True),
        sa.Column('anticipo_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('anticipo_minimo', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('disponible', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_productos_pedido_id'), 'productos_pedido', ['id'], unique=False)

    # Create pedidos table
    op.create_table('pedidos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('producto_pedido_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('cliente_nombre', sa.String(length=255), nullable=False),
        sa.Column('cliente_telefono', sa.String(length=20), nullable=True),
        sa.Column('cliente_email', sa.String(length=255), nullable=True),
        sa.Column('cantidad', sa.Integer(), nullable=True),
        sa.Column('precio_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('anticipo_pagado', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('saldo_pendiente', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=True),
        sa.Column('fecha_entrega_estimada', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_entrega_real', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notas_cliente', sa.Text(), nullable=True),
        sa.Column('notas_internas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['producto_pedido_id'], ['productos_pedido.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pedidos_id'), 'pedidos', ['id'], unique=False)

    # Create pagos_pedido table
    op.create_table('pagos_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('monto', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('metodo_pago', sa.String(length=20), nullable=False),
        sa.Column('tipo_pago', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pagos_pedido_id'), 'pagos_pedido', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_pagos_pedido_id'), table_name='pagos_pedido')
    op.drop_table('pagos_pedido')
    op.drop_index(op.f('ix_pedidos_id'), table_name='pedidos')
    op.drop_table('pedidos')
    op.drop_index(op.f('ix_productos_pedido_id'), table_name='productos_pedido')
    op.drop_table('productos_pedido')

