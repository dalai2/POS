from alembic import op
import sqlalchemy as sa


revision = "0007_sale_discounts_taxes_returns"
down_revision = "0006_payments_shifts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sales") as batch:
        batch.add_column(sa.Column("subtotal", sa.Numeric(10, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("return_of_id", sa.Integer(), nullable=True))
        batch.create_index("ix_sales_return_of_id", ["return_of_id"], unique=False)
        batch.create_foreign_key("fk_sales_return_of_id", "sales", ["return_of_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("sales") as batch:
        batch.drop_constraint("fk_sales_return_of_id", type_="foreignkey")
        batch.drop_index("ix_sales_return_of_id")
        batch.drop_column("return_of_id")
        batch.drop_column("tax_amount")
        batch.drop_column("tax_rate")
        batch.drop_column("discount_amount")
        batch.drop_column("subtotal")




