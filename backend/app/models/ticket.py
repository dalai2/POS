from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from datetime import datetime
from app.models.tenant import Base


class Ticket(Base):
    __tablename__ = "tickets"
    # Note: UniqueConstraint for (tenant_id, sale_id, kind) and (tenant_id, pedido_id, kind)
    # are now handled via partial indexes in the database migration

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sale_id = Column(Integer, nullable=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=True, index=True)
    kind = Column(String(50), nullable=False, default="sale")  # sale | payment | pedido-payment-{id} | pedido-abono-{id}
    html = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


