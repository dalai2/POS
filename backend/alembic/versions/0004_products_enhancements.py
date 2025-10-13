from alembic import op
import sqlalchemy as sa


revision = "0004_products_enhancements"
down_revision = "0003_tenant_billing_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(sa.Column("cost_price", sa.Numeric(10, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("category", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("barcode", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_products_category", ["category"], unique=False)
        batch_op.create_index("ix_products_barcode", ["barcode"], unique=False)
        batch_op.create_unique_constraint("uq_products_tenant_barcode", ["tenant_id", "barcode"])


def downgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_constraint("uq_products_tenant_barcode", type_="unique")
        batch_op.drop_index("ix_products_barcode")
        batch_op.drop_index("ix_products_category")
        batch_op.drop_column("created_at")
        batch_op.drop_column("active")
        batch_op.drop_column("barcode")
        batch_op.drop_column("category")
        batch_op.drop_column("cost_price")




