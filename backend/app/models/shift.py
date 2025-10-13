from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey

from app.models.tenant import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    opening_cash = Column(Numeric(10, 2), nullable=False, default=0)
    closing_cash = Column(Numeric(10, 2), nullable=True)




