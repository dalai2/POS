from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey

from app.models.tenant import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Movement type: "entrada" or "salida"
    movement_type = Column(String(20), nullable=False)
    
    # Quantity change (positive for entrada, negative for salida)
    quantity = Column(Integer, nullable=False)
    
    # Cost at time of movement (for entradas)
    cost = Column(Numeric(10, 2), nullable=True)
    
    # Notes/reason
    notes = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

