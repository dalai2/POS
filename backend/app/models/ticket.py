from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from datetime import datetime
from app.models.tenant import Base


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sale_id", "kind", name="uq_ticket_tenant_sale_kind"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sale_id = Column(Integer, nullable=True, index=True)
    kind = Column(String(50), nullable=False, default="sale")  # sale | payment | order
    html = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


