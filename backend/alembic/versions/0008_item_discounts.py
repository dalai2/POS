from alembic import op
import sqlalchemy as sa


revision = "0008_item_discounts"
down_revision = "0007_sale_discounts_taxes_returns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sale_items") as batch:
        batch.add_column(sa.Column("discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("sale_items") as batch:
        batch.drop_column("discount_amount")
        batch.drop_column("discount_pct")




