from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey

from app.models.tenant import Base


class MetalRate(Base):
    __tablename__ = "metal_rates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Metal type: "10k", "14k", "18k", "oro_italiano", "plata_gold", "plata_silver"
    metal_type = Column(String(50), nullable=False)
    
    # Rate per gram in currency
    rate_per_gram = Column(Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

