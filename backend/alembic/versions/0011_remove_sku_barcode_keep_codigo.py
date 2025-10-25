"""remove_sku_barcode_keep_codigo

Revision ID: 0011_remove_sku_barcode_keep_codigo
Revises: 0010_jewelry_store_transformation
Create Date: 2025-10-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0011_remove_sku_barcode_keep_codigo'
down_revision = '0010_jewelry_store_transformation'
branch_labels = None
depends_on = None


def upgrade():
    # Drop unique constraints on sku and barcode
    op.drop_constraint('uq_products_tenant_sku', 'products', type_='unique')
    op.drop_constraint('uq_products_tenant_barcode', 'products', type_='unique')
    
    # Drop columns sku and barcode from products
    op.drop_column('products', 'sku')
    op.drop_column('products', 'barcode')
    
    # Create unique constraint on codigo instead
    op.create_unique_constraint('uq_products_tenant_codigo', 'products', ['tenant_id', 'codigo'])
    
    # Drop sku column from sale_items and add codigo
    op.drop_column('sale_items', 'sku')
    op.add_column('sale_items', sa.Column('codigo', sa.String(length=100), nullable=True))


def downgrade():
    # Restore sale_items column
    op.drop_column('sale_items', 'codigo')
    op.add_column('sale_items', sa.Column('sku', sa.String(length=100), nullable=True))
    
    # Recreate sku and barcode columns
    op.add_column('products', sa.Column('sku', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('barcode', sa.String(length=100), nullable=True))
    
    # Recreate unique constraints
    op.create_unique_constraint('uq_products_tenant_sku', 'products', ['tenant_id', 'sku'])
    op.create_unique_constraint('uq_products_tenant_barcode', 'products', ['tenant_id', 'barcode'])
    
    # Drop codigo unique constraint
    op.drop_constraint('uq_products_tenant_codigo', 'products', type_='unique')

