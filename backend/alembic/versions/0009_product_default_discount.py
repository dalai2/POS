from alembic import op
import sqlalchemy as sa


revision = "0009_product_default_discount"
down_revision = "0008_item_discounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("default_discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.drop_column("default_discount_pct")




