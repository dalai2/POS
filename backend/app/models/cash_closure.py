from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, UniqueConstraint, JSON
from datetime import datetime, date
from app.models.tenant import Base


class CashClosure(Base):
    __tablename__ = "cash_closures"
    __table_args__ = (
        UniqueConstraint("tenant_id", "closure_date", name="uq_cash_closure_tenant_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    closure_date = Column(Date, nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Persist all metrics as-is
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


