"""jewelry_store_transformation

Revision ID: 0010_jewelry_store_transformation
Revises: 0009_product_default_discount
Create Date: 2025-10-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0010_jewelry_store_transformation'
down_revision = '0009_product_default_discount'
branch_labels = None
depends_on = None


def upgrade():
    # Create metal_rates table
    op.create_table(
        'metal_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('metal_type', sa.String(length=50), nullable=False),
        sa.Column('rate_per_gram', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metal_rates_id'), 'metal_rates', ['id'], unique=False)
    op.create_index(op.f('ix_metal_rates_tenant_id'), 'metal_rates', ['tenant_id'], unique=False)
    
    # Create inventory_movements table
    op.create_table(
        'inventory_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_movements_id'), 'inventory_movements', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_product_id'), 'inventory_movements', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_tenant_id'), 'inventory_movements', ['tenant_id'], unique=False)
    
    # Create credit_payments table
    op.create_table(
        'credit_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_payments_id'), 'credit_payments', ['id'], unique=False)
    op.create_index(op.f('ix_credit_payments_sale_id'), 'credit_payments', ['sale_id'], unique=False)
    op.create_index(op.f('ix_credit_payments_tenant_id'), 'credit_payments', ['tenant_id'], unique=False)
    
    # Add jewelry-specific columns to products table
    op.add_column('products', sa.Column('codigo', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('marca', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('modelo', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('color', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('quilataje', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('base', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('tipo_joya', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('talla', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('peso_gramos', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('products', sa.Column('descuento_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('products', sa.Column('precio_manual', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('costo', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('precio_venta', sa.Numeric(precision=10, scale=2), nullable=True))
    
    op.create_index(op.f('ix_products_codigo'), 'products', ['codigo'], unique=False)
    op.create_index(op.f('ix_products_quilataje'), 'products', ['quilataje'], unique=False)
    op.create_index(op.f('ix_products_tipo_joya'), 'products', ['tipo_joya'], unique=False)
    
    # Add jewelry store columns to sales table
    op.add_column('sales', sa.Column('tipo_venta', sa.String(length=20), nullable=True, server_default='contado'))
    op.add_column('sales', sa.Column('vendedor_id', sa.Integer(), nullable=True))
    op.add_column('sales', sa.Column('utilidad', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('sales', sa.Column('total_cost', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('sales', sa.Column('customer_name', sa.String(length=255), nullable=True))
    op.add_column('sales', sa.Column('customer_phone', sa.String(length=50), nullable=True))
    op.add_column('sales', sa.Column('customer_address', sa.String(length=500), nullable=True))
    op.add_column('sales', sa.Column('amount_paid', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('sales', sa.Column('credit_status', sa.String(length=20), nullable=True, server_default='pendiente'))
    
    op.create_foreign_key('fk_sales_vendedor', 'sales', 'users', ['vendedor_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_sales_tipo_venta'), 'sales', ['tipo_venta'], unique=False)
    op.create_index(op.f('ix_sales_vendedor_id'), 'sales', ['vendedor_id'], unique=False)


def downgrade():
    # Drop sales table indexes and columns
    op.drop_index(op.f('ix_sales_vendedor_id'), table_name='sales')
    op.drop_index(op.f('ix_sales_tipo_venta'), table_name='sales')
    op.drop_constraint('fk_sales_vendedor', 'sales', type_='foreignkey')
    op.drop_column('sales', 'credit_status')
    op.drop_column('sales', 'amount_paid')
    op.drop_column('sales', 'customer_address')
    op.drop_column('sales', 'customer_phone')
    op.drop_column('sales', 'customer_name')
    op.drop_column('sales', 'total_cost')
    op.drop_column('sales', 'utilidad')
    op.drop_column('sales', 'vendedor_id')
    op.drop_column('sales', 'tipo_venta')
    
    # Drop products table indexes and columns
    op.drop_index(op.f('ix_products_tipo_joya'), table_name='products')
    op.drop_index(op.f('ix_products_quilataje'), table_name='products')
    op.drop_index(op.f('ix_products_codigo'), table_name='products')
    op.drop_column('products', 'precio_venta')
    op.drop_column('products', 'costo')
    op.drop_column('products', 'precio_manual')
    op.drop_column('products', 'descuento_porcentaje')
    op.drop_column('products', 'peso_gramos')
    op.drop_column('products', 'talla')
    op.drop_column('products', 'tipo_joya')
    op.drop_column('products', 'base')
    op.drop_column('products', 'quilataje')
    op.drop_column('products', 'color')
    op.drop_column('products', 'modelo')
    op.drop_column('products', 'marca')
    op.drop_column('products', 'codigo')
    
    # Drop credit_payments table
    op.drop_index(op.f('ix_credit_payments_tenant_id'), table_name='credit_payments')
    op.drop_index(op.f('ix_credit_payments_sale_id'), table_name='credit_payments')
    op.drop_index(op.f('ix_credit_payments_id'), table_name='credit_payments')
    op.drop_table('credit_payments')
    
    # Drop inventory_movements table
    op.drop_index(op.f('ix_inventory_movements_tenant_id'), table_name='inventory_movements')
    op.drop_index(op.f('ix_inventory_movements_product_id'), table_name='inventory_movements')
    op.drop_index(op.f('ix_inventory_movements_id'), table_name='inventory_movements')
    op.drop_table('inventory_movements')
    
    # Drop metal_rates table
    op.drop_index(op.f('ix_metal_rates_tenant_id'), table_name='metal_rates')
    op.drop_index(op.f('ix_metal_rates_id'), table_name='metal_rates')
    op.drop_table('metal_rates')

