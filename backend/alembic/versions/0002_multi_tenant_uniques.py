from alembic import op
import sqlalchemy as sa


revision = "0002_multi_tenant_uniques"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users unique per tenant on email
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_email")
        batch_op.create_unique_constraint("uq_users_tenant_email", ["tenant_id", "email"])
        batch_op.create_index("ix_users_email", ["email"], unique=False)

    # Products unique per tenant on sku
    with op.batch_alter_table("products") as batch_op:
        batch_op.create_unique_constraint("uq_products_tenant_sku", ["tenant_id", "sku"])


def downgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_constraint("uq_products_tenant_sku", type_="unique")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_tenant_email", type_="unique")
        batch_op.drop_index("ix_users_email")
        batch_op.create_index("ix_users_email", "users", ["email"], unique=True)





