from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.tenant import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
        UniqueConstraint("tenant_id", "barcode", name="uq_products_tenant_barcode"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    cost_price = Column(Numeric(10, 2), nullable=False, default=0)
    stock = Column(Integer, nullable=False, default=0)
    category = Column(String(100), nullable=True, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    default_discount_pct = Column(Numeric(5, 2), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Jewelry-specific fields
    codigo = Column(String(100), nullable=True, index=True)  # Internal code
    marca = Column(String(100), nullable=True)  # Brand
    modelo = Column(String(100), nullable=True)  # Model
    color = Column(String(50), nullable=True)  # Color
    quilataje = Column(String(20), nullable=True, index=True)  # Karat (10k, 14k, 18k, etc)
    base = Column(String(50), nullable=True)  # Base material
    tipo_joya = Column(String(50), nullable=True, index=True)  # Jewelry type (ring, necklace, etc)
    talla = Column(String(20), nullable=True)  # Size
    peso_gramos = Column(Numeric(10, 3), nullable=True)  # Weight in grams
    descuento_porcentaje = Column(Numeric(5, 2), nullable=True)  # Discount percentage
    precio_manual = Column(Numeric(10, 2), nullable=True)  # Manual price override
    costo = Column(Numeric(10, 2), nullable=True)  # Cost (alias for cost_price for clarity)
    precio_venta = Column(Numeric(10, 2), nullable=True)  # Sale price (alias for price for clarity)

    tenant = relationship("Tenant")


