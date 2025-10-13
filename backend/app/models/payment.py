from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.models.tenant import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String(50), nullable=False)  # e.g., cash, card, voucher
    amount = Column(Numeric(10, 2), nullable=False, default=0)




