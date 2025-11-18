from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from datetime import datetime
from app.models.tenant import Base


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "venta_contado_id", "kind", name="uq_tickets_venta_contado"),
        UniqueConstraint("tenant_id", "apartado_id", "kind", name="uq_tickets_apartado"),
        UniqueConstraint("tenant_id", "pedido_id", "kind", name="uq_tickets_pedido"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sale_id = Column(Integer, nullable=True, index=True)  # Legacy: ventas de contado antiguas
    venta_contado_id = Column(Integer, ForeignKey("ventas_contado.id"), nullable=True, index=True)  # Ventas de contado
    apartado_id = Column(Integer, ForeignKey("apartados.id"), nullable=True, index=True)  # Apartados
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=True, index=True)  # Pedidos
    kind = Column(String(50), nullable=False, default="sale")  # sale | payment | pedido-payment-{id} | pedido-abono-{id}
    html = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


