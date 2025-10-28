from sqlalchemy import Column, Integer, String, UniqueConstraint, Boolean, DateTime
from datetime import datetime
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (UniqueConstraint("slug", name="uq_tenant_slug"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    plan = Column(String(100), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
