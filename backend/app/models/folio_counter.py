from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from app.models.tenant import Base


class FolioCounter(Base):
	__tablename__ = "folio_counters"
	__table_args__ = (
		UniqueConstraint("tenant_id", "tipo", name="uq_folio_counters_tenant_tipo"),
	)

	id = Column(Integer, primary_key=True, index=True)
	tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
	# tipo: 'VENTA' | 'APARTADO' | 'PEDIDO'
	tipo = Column(String(20), nullable=False, index=True)
	next_seq = Column(Integer, nullable=False, default=1)


