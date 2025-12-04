from datetime import datetime

from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.tenant import Base


class Apartado(Base):
    __tablename__ = "apartados"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    vendedor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    utilidad = Column(Numeric(10, 2), nullable=True, default=0)
    total_cost = Column(Numeric(10, 2), nullable=True, default=0)
    folio_apartado = Column(String(50), nullable=True, index=True)

    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_address = Column(String(500), nullable=True)
    notas_cliente = Column(Text, nullable=True)

    amount_paid = Column(Numeric(10, 2), nullable=True, default=0)
    credit_status = Column(String(20), nullable=True, default="pendiente")
    vip_discount_pct = Column(Numeric(5, 2), nullable=False, default=0)

    items = relationship("ItemApartado", back_populates="apartado", cascade="all, delete-orphan")


class ItemApartado(Base):
    __tablename__ = "items_apartado"

    id = Column(Integer, primary_key=True, index=True)
    apartado_id = Column(Integer, ForeignKey("apartados.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    codigo = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0)
    discount_pct = Column(Numeric(5, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_price = Column(Numeric(10, 2), nullable=False, default=0)

    product_snapshot = Column(JSONB, nullable=True)

    apartado = relationship("Apartado", back_populates="items")


