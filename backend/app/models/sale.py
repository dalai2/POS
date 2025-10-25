from datetime import datetime

from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship

from app.models.tenant import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    return_of_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Jewelry store fields
    tipo_venta = Column(String(20), nullable=True, default="contado", index=True)  # "contado" or "credito"
    vendedor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Salesperson
    utilidad = Column(Numeric(10, 2), nullable=True, default=0)  # Profit (total - total_cost)
    total_cost = Column(Numeric(10, 2), nullable=True, default=0)  # Total cost of items sold
    
    # Credit sale fields
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_address = Column(String(500), nullable=True)
    amount_paid = Column(Numeric(10, 2), nullable=True, default=0)  # Total paid so far
    credit_status = Column(String(20), nullable=True, default="pendiente")  # "pendiente" or "pagado"

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    codigo = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0)
    discount_pct = Column(Numeric(5, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_price = Column(Numeric(10, 2), nullable=False, default=0)

    sale = relationship("Sale", back_populates="items")


