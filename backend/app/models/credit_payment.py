from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey

from app.models.tenant import Base


class CreditPayment(Base):
    __tablename__ = "credit_payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    # Legacy reference (deprecado tras migración)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True, index=True)
    # Nueva referencia a apartados
    apartado_id = Column(Integer, ForeignKey("apartados.id"), nullable=True, index=True)
    
    # Payment amount (abono)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Payment method: "efectivo" or "tarjeta"
    payment_method = Column(String(20), nullable=False, default="efectivo")
    
    # User who registered the payment
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notes
    notes = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    