from alembic import op
import sqlalchemy as sa


revision = "0003_tenant_billing_fields"
down_revision = "0002_multi_tenant_uniques"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tenants") as batch_op:
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("plan", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tenants") as batch_op:
        batch_op.drop_column("created_at")
        batch_op.drop_column("stripe_subscription_id")
        batch_op.drop_column("stripe_customer_id")
        batch_op.drop_column("plan")
        batch_op.drop_column("is_active")





